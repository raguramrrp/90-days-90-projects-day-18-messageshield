import React from "react";

interface ConfusionMatrixProps {
  tn: number;
  fp: number;
  fn: number;
  tp: number;
}

export const ConfusionMatrix: React.FC<ConfusionMatrixProps> = ({
  tn,
  fp,
  fn,
  tp,
}) => {
  return (
    <div className="space-y-1.5">
      <div className="grid grid-cols-[72px_1fr_1fr] items-center gap-1.5 text-center text-[10px] font-medium text-zinc-500">
        <div />
        <div>Pred: Ham</div>
        <div>Pred: Spam</div>
      </div>

      <div className="grid grid-cols-[72px_1fr_1fr] items-stretch gap-1.5">
        <div className="flex items-center justify-end pr-1 text-right text-[10px] font-medium text-zinc-600">
          Actual Ham
        </div>
        <div className="rounded-md border border-emerald-200 bg-emerald-50/70 p-2 text-center">
          <div className="font-mono-safe text-base font-bold text-emerald-900">{tn}</div>
          <div className="text-[10px] text-emerald-700">True Ham (TN)</div>
        </div>
        <div className="rounded-md border border-amber-200 bg-amber-50/70 p-2 text-center">
          <div className="font-mono-safe text-base font-bold text-amber-900">{fp}</div>
          <div className="text-[10px] text-amber-700">False Pos (FP)</div>
        </div>
      </div>

      <div className="grid grid-cols-[72px_1fr_1fr] items-stretch gap-1.5">
        <div className="flex items-center justify-end pr-1 text-right text-[10px] font-medium text-zinc-600">
          Actual Spam
        </div>
        <div className="rounded-md border border-orange-200 bg-orange-50/70 p-2 text-center">
          <div className="font-mono-safe text-base font-bold text-orange-900">{fn}</div>
          <div className="text-[10px] text-orange-700">Missed (FN)</div>
        </div>
        <div className="rounded-md border border-zinc-300 bg-zinc-100 p-2 text-center">
          <div className="font-mono-safe text-base font-bold text-zinc-900">{tp}</div>
          <div className="text-[10px] text-zinc-600">True Spam (TP)</div>
        </div>
      </div>
    </div>
  );
};
