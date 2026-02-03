import { ChevronsLeftIcon, LogOutIcon, MessageCircleIcon, MonitorIcon, MoonIcon, PaletteIcon, PlusIcon, SettingsIcon, SunIcon } from "lucide-react";
import { useNavigate, useParams } from "react-router-dom";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuCheckboxItem,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuSub,
  DropdownMenuSubContent,
  DropdownMenuSubTrigger,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useAuth } from "@/hooks/use-auth";
import { useConversations } from "@/hooks/use-conversations";
import { useTheme } from "@/hooks/use-theme";
import { cn } from "@/lib/utils";
import { PanelHeader } from "./panel-header";

interface SidebarPanelProps {
  onCollapse?: () => void;
}

export function SidebarPanel({ onCollapse }: SidebarPanelProps) {
  const { user, signOut } = useAuth();
  const { preference, set: setTheme } = useTheme();
  const { conversations, create } = useConversations();
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const displayName = user?.user_metadata?.full_name ?? user?.email ?? "User";
  const avatar = user?.user_metadata?.avatar_url as string | undefined;

  const handleNewChat = async () => {
    try {
      const conv = await create("NQ");
      navigate(`/c/${conv.id}`);
    } catch (err) {
      console.error("Failed to create conversation:", err);
    }
  };

  return (
    <div className="flex h-full flex-col bg-sidebar">
      <PanelHeader>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="sm">
              {avatar && (
                <img
                  src={avatar}
                  alt=""
                  className="size-5 rounded-full"
                />
              )}
              {displayName}
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="start" className="w-48">
            <DropdownMenuItem>
              <SettingsIcon />
              Settings
            </DropdownMenuItem>
            <DropdownMenuSub>
              <DropdownMenuSubTrigger>
                <PaletteIcon />
                Theme
              </DropdownMenuSubTrigger>
              <DropdownMenuSubContent sideOffset={8}>
                <DropdownMenuGroup>
                  <DropdownMenuCheckboxItem
                    checked={preference === "system"}
                    onCheckedChange={() => setTheme("system")}
                  >
                    <MonitorIcon />
                    System
                  </DropdownMenuCheckboxItem>
                  <DropdownMenuCheckboxItem
                    checked={preference === "light"}
                    onCheckedChange={() => setTheme("light")}
                  >
                    <SunIcon />
                    Light
                  </DropdownMenuCheckboxItem>
                  <DropdownMenuCheckboxItem
                    checked={preference === "dark"}
                    onCheckedChange={() => setTheme("dark")}
                  >
                    <MoonIcon />
                    Dark
                  </DropdownMenuCheckboxItem>
                </DropdownMenuGroup>
              </DropdownMenuSubContent>
            </DropdownMenuSub>
            <DropdownMenuItem onClick={signOut}>
              <LogOutIcon />
              Sign out
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
        <Button variant="ghost" size="icon-sm" onClick={onCollapse} aria-label="Collapse sidebar">
          <ChevronsLeftIcon />
        </Button>
      </PanelHeader>
      <div className="flex flex-1 flex-col overflow-y-auto px-2">
        <div className="mt-12 flex flex-col gap-1">
          <span className="px-2 text-xs text-muted-foreground">Chats</span>
          <Button
            variant="ghost"
            size="sm"
            className="justify-start"
            onClick={handleNewChat}
          >
            <PlusIcon />
            New chat
          </Button>
          {conversations.map((conv) => (
            <Button
              key={conv.id}
              variant="ghost"
              size="sm"
              className={cn("justify-start", conv.id === id && "bg-accent")}
              onClick={() => navigate(`/c/${conv.id}`)}
            >
              <MessageCircleIcon />
              <span className="truncate">{conv.title}</span>
            </Button>
          ))}
        </div>
      </div>
    </div>
  );
}
