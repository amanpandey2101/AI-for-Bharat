"use client";
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@/components/ui/sidebar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "./ui/dropdown-menu";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "./ui/dialog";
import { Input } from "./ui/input";
import { Label } from "./ui/label";
import { Textarea } from "./ui/textarea";
import { Button } from "./ui/button";
import {
  ChevronDown,
  ChevronRight,
  Home,
  LogOut,
  Plug,
  Activity,
  Brain,
  Settings,
  Plus,
  FolderKanban,
  Check,
  Loader2,
  Pencil,
  Trash2,
  BookOpen,
} from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { useWorkspace } from "@/context/WorkspaceContext";
import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { toast } from "sonner";
import { deleteWorkspace, updateWorkspace } from "@/services/workspaces";

const navItems = [
  { title: "Dashboard", url: "/dashboard", icon: Home },
  { title: "Integrations", url: "/dashboard/integrations", icon: Plug },
  { title: "Activity Feed", url: "/dashboard/activity", icon: Activity },
  { title: "Decision Memory", url: "/dashboard/decisions", icon: Brain },
  { title: "Architecture (ADRs)", url: "/dashboard/adrs", icon: BookOpen },
  { title: "Settings", url: "/dashboard/settings", icon: Settings },
];

export function AppSidebar() {
  const { user, loading } = useAuth();
  const {
    workspaces,
    activeWorkspace,
    setActiveWorkspace,
    createWorkspace,
    refreshWorkspaces,
  } = useWorkspace();
  const pathname = usePathname();

  // Create dialog state
  const [createOpen, setCreateOpen] = useState(false);
  const [createName, setCreateName] = useState("");
  const [createDesc, setCreateDesc] = useState("");
  const [createLoading, setCreateLoading] = useState(false);

  // Edit dialog state
  const [editOpen, setEditOpen] = useState(false);
  const [editName, setEditName] = useState("");
  const [editDesc, setEditDesc] = useState("");
  const [editLoading, setEditLoading] = useState(false);

  // Delete confirm state
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [deleteLoading, setDeleteLoading] = useState(false);

  const handleCreate = async () => {
    if (!createName.trim()) return;
    setCreateLoading(true);
    try {
      await createWorkspace(createName.trim(), createDesc.trim());
      toast.success(`Workspace "${createName}" created!`);
      setCreateOpen(false);
      setCreateName("");
      setCreateDesc("");
    } catch (err: unknown) {
      const message =
        (err as { response?: { data?: { message?: string } } }).response?.data?.message || "Something went wrong. Try again.";
      toast.error(message);
    } finally {
      setCreateLoading(false);
    }
  };

  const handleEdit = async () => {
    if (!activeWorkspace || !editName.trim()) return;
    setEditLoading(true);
    try {
      await updateWorkspace(activeWorkspace.workspace_id, {
        name: editName.trim(),
        description: editDesc.trim(),
      });
      toast.success("Workspace updated");
      setEditOpen(false);
      refreshWorkspaces();
    } catch (err: unknown) {
      const message =
        (err as { response?: { data?: { message?: string } } }).response?.data?.message || "Something went wrong. Try again.";
      toast.error(message);
    } finally {
      setEditLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!activeWorkspace) return;
    setDeleteLoading(true);
    try {
      await deleteWorkspace(activeWorkspace.workspace_id);
      toast.success("Workspace deleted");
      setDeleteOpen(false);
      setActiveWorkspace(null);
      refreshWorkspaces();
    } catch (err: unknown) {
      const message =
        (err as { response?: { data?: { message?: string } } }).response?.data?.message || "Something went wrong. Try again.";
      toast.error(message);
    } finally {
      setDeleteLoading(false);
    }
  };

  const openEditDialog = () => {
    if (!activeWorkspace) return;
    setEditName(activeWorkspace.name);
    setEditDesc(activeWorkspace.description);
    setEditOpen(true);
  };

  return (
    <>
      <Sidebar>
        <SidebarHeader>
          <SidebarMenu>
            <SidebarMenuItem>
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <SidebarMenuButton className="cursor-pointer h-10">
                    <div className="flex items-center gap-2 flex-1 min-w-0">
                      <div className="w-6 h-6 rounded-md bg-gradient-to-br from-violet-500 to-indigo-600 flex items-center justify-center shrink-0">
                        <FolderKanban className="w-3.5 h-3.5 text-white" />
                      </div>
                      <span className="font-semibold truncate text-sm">
                        {activeWorkspace?.name || "No Workspace"}
                      </span>
                    </div>
                    <ChevronDown className="w-4 h-4 shrink-0 opacity-50" />
                  </SidebarMenuButton>
                </DropdownMenuTrigger>
                <DropdownMenuContent
                  className="w-[--radix-popper-anchor-width] min-w-[220px]"
                  align="start"
                >
                  {workspaces.length > 0 && (
                    <div className="px-2 py-1.5 text-[11px] font-medium text-muted-foreground uppercase tracking-wider">
                      Your Workspaces
                    </div>
                  )}
                  {workspaces.map((ws) => (
                    <DropdownMenuItem
                      key={ws.workspace_id}
                      onClick={() => setActiveWorkspace(ws)}
                      className="cursor-pointer"
                    >
                      <div className="flex items-center gap-2 w-full">
                        <div className="w-5 h-5 rounded bg-violet-100 flex items-center justify-center shrink-0">
                          <FolderKanban className="w-3 h-3 text-violet-600" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium truncate">{ws.name}</p>
                          <p className="text-[11px] text-muted-foreground truncate">
                            {ws.resources.length} resource{ws.resources.length !== 1 ? "s" : ""}
                          </p>
                        </div>
                        {activeWorkspace?.workspace_id === ws.workspace_id && (
                          <Check className="w-4 h-4 text-emerald-600 shrink-0" />
                        )}
                      </div>
                    </DropdownMenuItem>
                  ))}

                  <DropdownMenuSeparator />

                  {activeWorkspace && (
                    <>
                      <DropdownMenuItem
                        onClick={openEditDialog}
                        className="cursor-pointer"
                      >
                        <Pencil className="w-3.5 h-3.5 mr-2 text-muted-foreground" />
                        Edit Workspace
                      </DropdownMenuItem>
                      <DropdownMenuItem
                        onClick={() => setDeleteOpen(true)}
                        className="cursor-pointer text-red-600 focus:text-red-600"
                      >
                        <Trash2 className="w-3.5 h-3.5 mr-2" />
                        Delete Workspace
                      </DropdownMenuItem>
                      <DropdownMenuSeparator />
                    </>
                  )}

                  <DropdownMenuItem
                    onClick={() => setCreateOpen(true)}
                    className="cursor-pointer"
                  >
                    <Plus className="w-3.5 h-3.5 mr-2 text-violet-600" />
                    <span className="font-medium">New Workspace</span>
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </SidebarMenuItem>
          </SidebarMenu>
        </SidebarHeader>

        <SidebarContent>
          <SidebarGroup>
            <SidebarGroupLabel>Navigation</SidebarGroupLabel>
            <SidebarGroupContent>
              <SidebarMenu>
                {navItems.map((item) => {
                  const isActive = pathname === item.url;
                  return (
                    <SidebarMenuItem key={item.title}>
                      <SidebarMenuButton asChild isActive={isActive}>
                        <Link href={item.url}>
                          <item.icon className="w-4 h-4" />
                          <span>{item.title}</span>
                        </Link>
                      </SidebarMenuButton>
                    </SidebarMenuItem>
                  );
                })}
              </SidebarMenu>
            </SidebarGroupContent>
          </SidebarGroup>

          {/* Connected resources for active workspace */}
          {activeWorkspace && activeWorkspace.resources.length > 0 && (
            <SidebarGroup>
              <SidebarGroupLabel>Connected Resources</SidebarGroupLabel>
              <SidebarGroupContent>
                <div className="px-3 space-y-1.5">
                  {activeWorkspace.resources.map((r) => (
                    <div
                      key={`${r.platform}-${r.resource_id}`}
                      className="flex items-center gap-2 text-xs text-muted-foreground py-0.5"
                    >
                      <span
                        className={`w-1.5 h-1.5 rounded-full shrink-0 ${
                          r.platform === "github"
                            ? "bg-gray-800"
                            : r.platform === "gitlab"
                            ? "bg-orange-500"
                            : r.platform === "slack"
                            ? "bg-purple-500"
                            : "bg-blue-500"
                        }`}
                      />
                      <span className="truncate flex-1">{r.resource_name}</span>
                      <span className="text-[10px] uppercase opacity-50">
                        {r.platform}
                      </span>
                    </div>
                  ))}
                </div>
              </SidebarGroupContent>
            </SidebarGroup>
          )}
        </SidebarContent>

        {!loading && (
          <SidebarFooter>
            <SidebarMenu>
              <SidebarMenuItem>
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <SidebarMenuButton className="cursor-pointer flex flex-row justify-between bg-gray-200 p-4 h-12">
                      <div className="flex flex-row gap-2 items-center">
                        <Image
                          src={user?.avatar_url || "/avatar.svg"}
                          alt="user-image"
                          width={36}
                          height={36}
                          className="w-9 h-9 rounded-full object-cover"
                        />{" "}
                        {user?.name}
                      </div>
                      <ChevronRight />
                    </SidebarMenuButton>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent className="w-[--radix-popper-anchor-width]">
                    <DropdownMenuItem className="cursor-pointer">
                      <LogOut color="red" /> Logout
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </SidebarMenuItem>
            </SidebarMenu>
          </SidebarFooter>
        )}
      </Sidebar>

      {/* ── Create Workspace Dialog ─────────────────────────────── */}
      <Dialog open={createOpen} onOpenChange={setCreateOpen}>
        <DialogContent className="sm:max-w-[480px]">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-violet-500 to-indigo-600 flex items-center justify-center">
                <FolderKanban className="w-4 h-4 text-white" />
              </div>
              Create Workspace
            </DialogTitle>
            <DialogDescription>
              A workspace groups related repositories, Slack channels, and Jira
              projects together. All decisions discovered within a workspace are
              scoped to it.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-2">
            <div className="space-y-2">
              <Label htmlFor="ws-name">Name</Label>
              <Input
                id="ws-name"
                placeholder="e.g. Memora Platform, Backend Services..."
                value={createName}
                onChange={(e) => setCreateName(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleCreate()}
                autoFocus
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="ws-desc">Description (optional)</Label>
              <Textarea
                id="ws-desc"
                placeholder="What is this workspace for?"
                value={createDesc}
                onChange={(e) => setCreateDesc(e.target.value)}
                rows={3}
              />
            </div>
          </div>

          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setCreateOpen(false)}
              className="cursor-pointer"
            >
              Cancel
            </Button>
            <Button
              onClick={handleCreate}
              disabled={!createName.trim() || createLoading}
              className="cursor-pointer bg-violet-600 hover:bg-violet-700"
            >
              {createLoading && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
              Create Workspace
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* ── Edit Workspace Dialog ──────────────────────────────── */}
      <Dialog open={editOpen} onOpenChange={setEditOpen}>
        <DialogContent className="sm:max-w-[480px]">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Pencil className="w-4 h-4 text-muted-foreground" />
              Edit Workspace
            </DialogTitle>
            <DialogDescription>
              Update workspace name and description.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-2">
            <div className="space-y-2">
              <Label htmlFor="ws-edit-name">Name</Label>
              <Input
                id="ws-edit-name"
                value={editName}
                onChange={(e) => setEditName(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleEdit()}
                autoFocus
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="ws-edit-desc">Description</Label>
              <Textarea
                id="ws-edit-desc"
                value={editDesc}
                onChange={(e) => setEditDesc(e.target.value)}
                rows={3}
              />
            </div>
          </div>

          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setEditOpen(false)}
              className="cursor-pointer"
            >
              Cancel
            </Button>
            <Button
              onClick={handleEdit}
              disabled={!editName.trim() || editLoading}
              className="cursor-pointer"
            >
              {editLoading && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
              Save Changes
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* ── Delete Workspace Confirm Dialog ────────────────────── */}
      <Dialog open={deleteOpen} onOpenChange={setDeleteOpen}>
        <DialogContent className="sm:max-w-[400px]">
          <DialogHeader>
            <DialogTitle className="text-red-600 flex items-center gap-2">
              <Trash2 className="w-4 h-4" />
              Delete Workspace
            </DialogTitle>
            <DialogDescription>
              Are you sure you want to delete{" "}
              <strong>{activeWorkspace?.name}</strong>? This will remove all
              workspace resource connections. Decisions and events already
              captured will not be deleted.
            </DialogDescription>
          </DialogHeader>

          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setDeleteOpen(false)}
              className="cursor-pointer"
            >
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={handleDelete}
              disabled={deleteLoading}
              className="cursor-pointer"
            >
              {deleteLoading && (
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              )}
              Delete Workspace
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
