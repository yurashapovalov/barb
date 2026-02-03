import { ChevronsLeftIcon, LogOutIcon, MessageCircleIcon, MoonIcon, PlusIcon, SettingsIcon, SunIcon } from "lucide-react";
import { useCallback, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
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
  const { theme, toggle: toggleTheme } = useTheme();
  const { conversations, create } = useConversations();
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const displayName = user?.user_metadata?.full_name ?? user?.email ?? "User";
  const avatar = user?.user_metadata?.avatar_url as string | undefined;

  const [menuOpen, setMenuOpen] = useState(false);

  const handleNewChat = useCallback(async () => {
    try {
      const conv = await create("NQ");
      navigate(`/c/${conv.id}`);
    } catch (err) {
      console.error("Failed to create conversation:", err);
    }
  }, [create, navigate]);

  return (
    <div className="flex h-full flex-col bg-sidebar">
      <PanelHeader>
        <Popover open={menuOpen} onOpenChange={setMenuOpen}>
          <PopoverTrigger asChild>
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
          </PopoverTrigger>
          <PopoverContent align="start" className="w-48 p-1">
            <Button variant="ghost" size="sm" className="w-full justify-start" onClick={() => setMenuOpen(false)}>
              <SettingsIcon />
              Settings
            </Button>
            <Button variant="ghost" size="sm" className="w-full justify-start" onClick={() => { toggleTheme(); setMenuOpen(false); }}>
              {theme === "dark" ? <SunIcon /> : <MoonIcon />}
              {theme === "dark" ? "Light mode" : "Dark mode"}
            </Button>
            <Button variant="ghost" size="sm" className="w-full justify-start" onClick={() => { signOut(); setMenuOpen(false); }}>
              <LogOutIcon />
              Sign out
            </Button>
          </PopoverContent>
        </Popover>
        <Button variant="ghost" size="icon-sm" onClick={onCollapse}>
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
