"use client";

import React, { useState } from "react";
import { Modal } from "./modal";
import { Input, Textarea, Select } from "./input";
import { Button } from "./button";
import { Badge } from "./badge";
import type { Task, TaskCreate, TaskUpdate } from "@/types";

interface TaskModalProps {
  isOpen: boolean;
  onClose: () => void;
  task?: Task | null;
  onSave: (task: TaskCreate | TaskUpdate) => void;
}

export const TaskModal = ({ isOpen, onClose, task, onSave }: TaskModalProps) => {
  const [formData, setFormData] = useState({
    title: task?.title || "",
    project: task?.project || "General",
    priority: task?.priority || "Medium",
    status: task?.status || "todo",
    due: task?.due_date || new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString().split("T")[0],
  });

  React.useEffect(() => {
    if (task) {
      setFormData({
        title: task.title,
        project: task.project,
        priority: task.priority,
        status: task.status,
        due: task.due_date,
      });
    } else {
      setFormData({
        title: "",
        project: "General",
        priority: "Medium",
        status: "todo",
        due: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString().split("T")[0],
      });
    }
  }, [task, isOpen]);

  const handleSave = () => {
    if (!formData.title.trim()) return;
    if (task) {
      onSave({ ...formData, id: task.id } as TaskUpdate);
    } else {
      onSave(formData as TaskCreate);
    }
    onClose();
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={task ? "Edit task" : "New task"}>
      <div className="space-y-3">
        <Input
          value={formData.title}
          onChange={e => setFormData({ ...formData, title: e.target.value })}
          placeholder="Task title"
          autoFocus
        />
        <Input
          value={formData.project}
          onChange={e => setFormData({ ...formData, project: e.target.value })}
          placeholder="Project"
        />
        <div className="grid grid-cols-3 gap-2">
          <Select
            value={formData.priority}
            onChange={e => setFormData({ ...formData, priority: e.target.value })}
            options={["High", "Medium", "Low"].map(x => ({ value: x, label: x }))}
          />
          <Select
            value={formData.status}
            onChange={e => setFormData({ ...formData, status: e.target.value })}
            options={[
              { value: "todo", label: "To do" },
              { value: "doing", label: "In progress" },
              { value: "done", label: "Done" },
            ]}
          />
          <Input
            type="date"
            value={formData.due}
            onChange={e => setFormData({ ...formData, due: e.target.value })}
          />
        </div>
        <Button className="w-full" onClick={handleSave} disabled={!formData.title.trim()}>
          Save task
        </Button>
      </div>
    </Modal>
  );
}