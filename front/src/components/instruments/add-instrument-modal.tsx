import { useCallback, useEffect, useRef, useState } from "react";
import { CheckIcon } from "lucide-react";
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from "@/components/ui/command";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { useInstruments } from "@/hooks/use-instruments";
import { listInstruments } from "@/lib/api";
import type { Instrument } from "@/types";

const CATEGORIES: Record<string, string> = {
  index: "Index",
  energy: "Energy",
  metals: "Metals",
  treasury: "Treasury",
  currency: "Currency",
  agriculture: "Agriculture",
  crypto: "Crypto",
};

interface AddInstrumentModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function AddInstrumentModal({ open, onOpenChange }: AddInstrumentModalProps) {
  const { instruments: userInstruments, add } = useInstruments();
  const addedSymbols = new Set(userInstruments.map((i) => i.instrument));

  const [results, setResults] = useState<Instrument[]>([]);
  const [loading, setLoading] = useState(false);
  const [search, setSearch] = useState("");
  const debounceRef = useRef<ReturnType<typeof setTimeout>>(undefined);

  const fetchInstruments = useCallback((query: string) => {
    setLoading(true);
    listInstruments(query || undefined)
      .then(setResults)
      .catch((err) => console.error("Failed to search instruments:", err))
      .finally(() => setLoading(false));
  }, []);

  // Load all on open
  useEffect(() => {
    if (open) {
      setSearch("");
      fetchInstruments("");
    }
  }, [open, fetchInstruments]);

  // Debounced search
  const handleSearch = (value: string) => {
    setSearch(value);
    clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => fetchInstruments(value), 200);
  };

  // Group results by category
  const grouped = new Map<string, Instrument[]>();
  for (const inst of results) {
    const group = grouped.get(inst.category) ?? [];
    group.push(inst);
    grouped.set(inst.category, group);
  }

  const handleSelect = async (symbol: string) => {
    if (addedSymbols.has(symbol)) return;
    try {
      await add(symbol);
    } catch (err) {
      console.error("Failed to add instrument:", err);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="overflow-hidden p-0 sm:max-w-lg">
        <DialogHeader className="sr-only">
          <DialogTitle>Add instrument</DialogTitle>
          <DialogDescription>Search and add instruments to your workspace.</DialogDescription>
        </DialogHeader>
        <Command shouldFilter={false}>
          <CommandInput
            placeholder="Search by symbol or name..."
            value={search}
            onValueChange={handleSearch}
          />
          <CommandList>
            {loading && results.length === 0 && (
              <div className="py-6 text-center text-sm text-muted-foreground">Loading...</div>
            )}
            <CommandEmpty>No instruments found.</CommandEmpty>
            {[...grouped.entries()].map(([category, instruments]) => (
              <CommandGroup key={category} heading={CATEGORIES[category] ?? category}>
                {instruments.map((inst) => {
                  const added = addedSymbols.has(inst.symbol);
                  return (
                    <CommandItem
                      key={inst.symbol}
                      value={inst.symbol}
                      onSelect={() => handleSelect(inst.symbol)}
                      className="flex items-center gap-3"
                    >
                      {inst.image_url && (
                        <img src={inst.image_url} alt="" className="size-5 rounded-full" />
                      )}
                      <span className="font-medium">{inst.symbol}</span>
                      <span className="text-muted-foreground">{inst.name}</span>
                      <span className="ml-auto text-xs text-muted-foreground">{inst.exchange}</span>
                      {added && <CheckIcon className="size-4 text-green-500" />}
                    </CommandItem>
                  );
                })}
              </CommandGroup>
            ))}
          </CommandList>
        </Command>
      </DialogContent>
    </Dialog>
  );
}
