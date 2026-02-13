import { useContext } from "react";
import { InstrumentsContext } from "@/components/instruments/instruments-context";

export function useInstruments() {
  const ctx = useContext(InstrumentsContext);
  if (!ctx) throw new Error("useInstruments must be used within InstrumentsProvider");
  return ctx;
}
