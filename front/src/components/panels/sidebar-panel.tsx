import { useState } from "react";
import { ChevronsLeftIcon, LogOutIcon, MonitorIcon, MoonIcon, PaletteIcon, PlusIcon, SettingsIcon, SunIcon } from "lucide-react";
import { useNavigate, useParams } from "react-router-dom";
import { AddInstrumentModal } from "@/components/instruments/add-instrument-modal";
import { Avatar } from "@/components/ui/avatar";
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
import { useInstruments } from "@/hooks/use-instruments";
import { useTheme } from "@/hooks/use-theme";
import { cn } from "@/lib/utils";
import { PanelHeader } from "./panel-header";

interface SidebarPanelProps {
  onCollapse?: () => void;
}

export function SidebarPanel({ onCollapse }: SidebarPanelProps) {
  const { user, signOut } = useAuth();
  const { preference, set: setTheme } = useTheme();
  const { instruments } = useInstruments();
  const { conversations } = useConversations();
  const { symbol, id } = useParams<{ symbol: string; id: string }>();
  const navigate = useNavigate();
  const [addModalOpen, setAddModalOpen] = useState(false);
  const displayName = user?.user_metadata?.full_name ?? user?.email ?? "User";
  const avatar = user?.user_metadata?.avatar_url as string | undefined;

  return (
    <div className="flex h-full flex-col bg-sidebar">
      <PanelHeader>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="sm">
              <Avatar size="xs" src={avatar} fallback={displayName.slice(0, 2)} />
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
          <span className="px-2 text-xs text-muted-foreground">Symbols</span>
          <Button
            variant="ghost"
            size="sm"
            className="justify-start"
            onClick={() => setAddModalOpen(true)}
          >
            <PlusIcon />
            Add symbol
          </Button>
          {instruments.map((inst) => (
            <Button
              key={inst.instrument}
              variant="ghost"
              size="sm"
              className={cn("justify-start gap-2", inst.instrument === symbol && !id && "bg-accent")}
              onClick={() => navigate(`/i/${inst.instrument}`)}
            >
              <Avatar size="xs" src={inst.image_url} fallback={inst.instrument.slice(0, 2)} />
              <span className="font-medium">{inst.instrument}</span>
              <span className="text-muted-foreground">·</span>
              <span className="truncate text-muted-foreground">{inst.name}</span>
            </Button>
          ))}
        </div>
        {conversations.length > 0 && (
          <div className="mt-4 flex flex-col gap-1">
            <span className="px-2 text-xs text-muted-foreground">Chats</span>
            {conversations.map((conv) => {
              const img = instruments.find((i) => i.instrument === conv.instrument)?.image_url;
              return (
                <Button
                  key={conv.id}
                  variant="ghost"
                  size="sm"
                  className={cn("justify-start gap-2", conv.id === id && "bg-accent")}
                  onClick={() => navigate(`/i/${conv.instrument}/c/${conv.id}`)}
                >
                  <Avatar size="xs" src={img} fallback={conv.instrument.slice(0, 2)} />
                  <span className="truncate">{conv.title}</span>
                </Button>
              );
            })}
          </div>
        )}
      </div>
      <AddInstrumentModal
        open={addModalOpen}
        onOpenChange={setAddModalOpen}
        onAdded={(sym) => navigate(`/i/${sym}`)}
      />
    </div>
  );
}
