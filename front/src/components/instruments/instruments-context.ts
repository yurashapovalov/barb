import { createContext } from "react";
import type { UserInstrument } from "@/types";

export interface InstrumentsContextValue {
  instruments: UserInstrument[];
  loading: boolean;
  add: (symbol: string) => Promise<void>;
  remove: (symbol: string) => Promise<void>;
}

export const InstrumentsContext = createContext<InstrumentsContextValue | null>(null);
