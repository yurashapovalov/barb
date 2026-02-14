import { createContext } from "react";
import type { Instrument, UserInstrument } from "@/types";

export interface InstrumentsContextValue {
  instruments: UserInstrument[];
  loading: boolean;
  error: string | null;
  add: (instrument: Instrument) => Promise<void>;
  remove: (symbol: string) => Promise<void>;
  retry: () => void;
}

export const InstrumentsContext = createContext<InstrumentsContextValue | null>(null);
