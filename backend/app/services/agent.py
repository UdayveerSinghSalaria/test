from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid

from app.models.task import Task
from app.models.proposal import Proposal, ProposalStatus
from app.models.agent_run import AgentRun, AgentRunStatus
from app.models.activity import Activity
from app.models.user import User
from app.services.nemotron import NemotronService, PlanResult, get_nemotron_service
from app.services.auth import AuthService
from app.services.imap_service import IMAPService
from app.config import settings


class AgentService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.nemotron = get_nemotron_service()

    async def generate_plan(
        self,
        command: str,
        webpage_url: Optional[str] = None,
        webpage_text: Optional[str] = None,
        source: str = "Agent Studio",
        current_user: Optional[User] = None,
    ) -> dict:
        """Generate an action plan and create a proposal."""
        # Get existing tasks for context
        query = select(Task).order_by(Task.due)
        if current_user:
            query = query.where(Task.user_id == current_user.id)
        result = await self.db.execute(query)
        existing_tasks = result.scalars().all()

        # Auto-fetch emails if command mentions email-related keywords
        email_context = ""
        if current_user:
            email_keywords = ["email", "mail", "inbox", "message", "read my", "summarize my", "check my"]
            needs_email = any(k in command.lower() for k in email_keywords)
            
            if needs_email:
                auth = AuthService(self.db)
                email_account = await auth.get_user_email_account(current_user.id)
                if email_account:
                    try:
                        imap = IMAPService(email_account)
                        # Quick timeout - if IMAP takes too long, skip email context
                        import asyncio
                        try:
                            emails = await asyncio.wait_for(
                                asyncio.to_thread(imap.fetch_recent, 10, 3),
                                timeout=5.0
                            )
                            if emails:
                                email_context = "\n\n".join([
                                    f"From: {e.from_}\nSubject: {e.subject}\nDate: {e.date}\nSnippet: {e.snippet}"
                                    for e in emails
                                ])
                        except asyncio.TimeoutError:
                            print(f"[Agent] IMAP fetch timed out, skipping email context")
                        except Exception as e:
                            print(f"[Agent] Failed to fetch emails: {e}")
                    except Exception as e:
                        print(f"[Agent] IMAP error: {e}")

        # Combine webpage_text with email_context
        combined_text = ""
        if webpage_text:
            combined_text += webpage_text
        if email_context:
            if combined_text:
                combined_text += "\n\n---\n\n"
            combined_text += f"USER'S RECENT EMAILS:\n{email_context}"

        # Generate plan via Nemotron
        plan_result: PlanResult = await self.nemotron.generate_action_plan(
            command=command,
            webpage_url=webpage_url,
            webpage_text=combined_text if combined_text else None,
            existing_tasks=existing_tasks,
        )

        # Create proposal
        proposal = Proposal(
            id=f"prop-{uuid.uuid4().hex[:12]}",
            user_id=current_user.id if current_user else None,
            title=command,
            source=source,
            url=webpage_url or "",
            summary=plan_result.summary,
            tasks=plan_result.tasks,
            status=ProposalStatus.PENDING,
        )
        self.db.add(proposal)

        # Create agent run
        run = AgentRun(
            id=f"run-{uuid.uuid4().hex[:12]}",
            user_id=current_user.id if current_user else None,
            command=command,
            status=AgentRunStatus.PLANNED,
            raw_input=f"{command}{f' (URL: {webpage_url})' if webpage_url else ''}",
            output_summary=plan_result.summary,
            proposal_id=proposal.id,
        )
        self.db.add(run)

        # Log activity
        activity = Activity(
            id=f"act-{uuid.uuid4().hex[:12]}",
            user_id=current_user.id if current_user else None,
            type="Plan",
            title=f"AI Plan drafted: {proposal.title}",
            detail=f"{len(plan_result.tasks)} proposed actions awaiting approval",
            source=source,
            status="Pending",
        )
        self.db.add(activity)

        await self.db.commit()
        await self.db.refresh(proposal)
        await self.db.refresh(run)

        return {
            "success": True,
            "proposalId": proposal.id,
            "runId": run.id,
            "summary": plan_result.summary,
            "tasks": plan_result.tasks,
            "isSimulated": plan_result.is_simulated,
            "warning": plan_result.warning,
        }

    async def get_proposals(self, status: Optional[str] = None, current_user: Optional[User] = None) -> List[Proposal]:
        """Get proposals with optional status filter."""
        from sqlalchemy import desc
        query = select(Proposal).order_by(desc(Proposal.created_at))
        if current_user:
            query = query.where(Proposal.user_id == current_user.id)
        if status and status != "All":
            query = query.where(Proposal.status == status)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_proposal(self, proposal_id: str, current_user: Optional[User] = None) -> Optional[Proposal]:
        """Get a single proposal by ID."""
        query = select(Proposal).where(Proposal.id == proposal_id)
        if current_user:
            query = query.where(Proposal.user_id == current_user.id)
        result = await self.db.execute(query)
        return result.scalars().first()

    async def update_proposal(self, proposal_id: str, patch: dict, current_user: Optional[User] = None) -> Optional[Proposal]:
        """Update a proposal."""
        proposal = await self.get_proposal(proposal_id, current_user)
        if not proposal:
            return None
        for key, value in patch.items():
            if hasattr(proposal, key):
                setattr(proposal, key, value)
        await self.db.commit()
        await self.db.refresh(proposal)
        return proposal

    async def decide_proposal(
        self,
        proposal_id: str,
        approve: bool,
        edited_tasks: List[dict],
        current_user: Optional[User] = None,
    ) -> dict:
        """Approve or reject a proposal."""
        proposal = await self.get_proposal(proposal_id, current_user)
        if not proposal:
            raise ValueError(f"Proposal {proposal_id} not found")

        if proposal.status != ProposalStatus.PENDING:
            raise ValueError(f"Proposal {proposal_id} has already been {proposal.status.value}")

        # Convert Pydantic models to dicts if needed
        action_list = []
        if edited_tasks:
            for t in edited_tasks:
                if hasattr(t, 'model_dump'):
                    action_list.append(t.model_dump())
                elif hasattr(t, 'dict'):
                    action_list.append(t.dict())
                else:
                    action_list.append(t)
        else:
            action_list = proposal.tasks

        if not approve:
            # Reject
            proposal.status = ProposalStatus.REJECTED
            proposal.tasks = action_list
            proposal.decided_at = __import__('datetime').datetime.now(__import__('datetime').timezone.utc)
            proposal.execution_result = {"executed": False, "reason": "Proposal rejected by user"}

            activity = Activity(
                id=f"act-{uuid.uuid4().hex[:12]}",
                user_id=current_user.id if current_user else None,
                type="Approval",
                title=f"Rejected: {proposal.title}",
                detail="No tasks created",
                source="Approvals",
                status="Rejected",
            )
            self.db.add(activity)

            await self.db.commit()
            return {"success": True, "status": "rejected", "proposalId": proposal_id, "createdTasks": []}

        # Approve - create tasks
        from datetime import date
        from app.models.task import TaskPriority, TaskStatus
        created_tasks = []
        for t in action_list:
            due_str = t.get("due", "2026-11-20")
            try:
                due_date = date.fromisoformat(due_str)
            except ValueError:
                due_date = date.today()
            
            # Convert priority string to enum
            priority_str = t.get("priority", "Medium")
            try:
                priority = TaskPriority(priority_str)
            except ValueError:
                priority = TaskPriority.MEDIUM
            
            task = Task(
                id=f"t-{uuid.uuid4().hex[:12]}",
                user_id=current_user.id if current_user else None,
                title=t.get("title", ""),
                project=t.get("project", "General"),
                priority=priority,
                status=TaskStatus.TODO,
                due=due_date,
            )
            self.db.add(task)
            created_tasks.append(task)

        proposal.status = ProposalStatus.APPROVED
        proposal.tasks = action_list
        proposal.decided_at = __import__('datetime').datetime.now(__import__('datetime').timezone.utc)
        proposal.execution_result = {"executed": True, "tasksCreated": len(created_tasks)}

        activity = Activity(
            id=f"act-{uuid.uuid4().hex[:12]}",
            user_id=current_user.id if current_user else None,
            type="Approval",
            title=f"Approved: {proposal.title}",
            detail=f"{len(created_tasks)} tasks created in My Space",
            source="Approvals",
            status="Completed",
        )
        self.db.add(activity)

        await self.db.commit()

        return {
            "success": True,
            "status": "approved",
            "proposalId": proposal_id,
            "createdTasks": [t.to_dict() for t in created_tasks],
        }