import React from "react";
import { Maximize2, RotateCcw, Smartphone, Wifi } from "lucide-react";
import textvigilLogo from "../assets/textvigil-logo.png";
import type { PreviewMode } from "../types/messageshield";

interface PhoneFrameShellProps {
  previewMode: PreviewMode;
  onChangePreviewMode: (mode: PreviewMode) => void;
  onResetViewport: () => void;
  scrollContainerRef: React.RefObject<HTMLDivElement | null>;
  header: React.ReactNode;
  bottomNav: React.ReactNode;
  appearanceMode?: "warm_light" | "crisp_slate";
  children: React.ReactNode;
}

export const PhoneFrameShell: React.FC<PhoneFrameShellProps> = ({
  previewMode,
  onChangePreviewMode,
  onResetViewport,
  scrollContainerRef,
  header,
  bottomNav,
  appearanceMode = "warm_light",
  children,
}) => {
  const screenBg = appearanceMode === "crisp_slate" ? "bg-white" : "bg-[#F5F5F2]";
  const isPhone = previewMode === "phone";

  return (
    <div className="min-h-dvh w-full bg-[#E8E8E3]">
      {/* Desktop/Tablet Preview Controls Bar (hidden on mobile < 768px) */}
      <div className="hidden h-12 w-full items-center justify-between border-b border-zinc-200 bg-white px-5 md:flex">
        <div className="flex items-center gap-2.5">
          <img
            src={textvigilLogo}
            alt="TextVigil logo"
            className="h-7 w-7 rounded-md"
          />
          <span className="text-sm font-semibold tracking-tight text-zinc-900">
            TextVigil
          </span>
        </div>

        <div className="flex items-center gap-2">
          <div
            className="inline-flex rounded-md border border-zinc-200 bg-zinc-100 p-0.5"
            role="group"
            aria-label="Viewport preview mode"
          >
            <button
              type="button"
              onClick={() => onChangePreviewMode("phone")}
              data-testid="toggle-phone-preview"
              className={`inline-flex items-center gap-1.5 rounded px-2.5 py-1 text-xs font-medium transition ${
                isPhone
                  ? "bg-white text-zinc-900 shadow-2xs"
                  : "text-zinc-600 hover:text-zinc-900"
              }`}
            >
              <Smartphone className="h-3.5 w-3.5" />
              Phone Preview
            </button>
            <button
              type="button"
              onClick={() => onChangePreviewMode("fullscreen")}
              data-testid="toggle-fullscreen-preview"
              className={`inline-flex items-center gap-1.5 rounded px-2.5 py-1 text-xs font-medium transition ${
                !isPhone
                  ? "bg-white text-zinc-900 shadow-2xs"
                  : "text-zinc-600 hover:text-zinc-900"
              }`}
            >
              <Maximize2 className="h-3.5 w-3.5" />
              Full Screen
            </button>
          </div>

          <button
            type="button"
            onClick={onResetViewport}
            data-testid="reset-viewport"
            title="Reset to default phone viewport"
            className="inline-flex items-center gap-1 rounded-md border border-zinc-200 bg-white px-2.5 py-1 text-xs font-medium text-zinc-700 transition hover:bg-zinc-50"
          >
            <RotateCcw className="h-3.5 w-3.5" />
            Reset
          </button>
        </div>
      </div>

      {/* Single Responsive Stage wrapping ONE mobile app viewport instance */}
      <div
        className={`flex w-full justify-center ${
          isPhone
            ? "md:min-h-[calc(100dvh-3rem)] md:items-center md:px-4 md:py-3"
            : "md:h-[calc(100dvh-3rem)]"
        }`}
      >
        <div className="relative flex w-full justify-center md:w-auto">
          {/* iPhone 18 Pro Titanium Hardware Side Keys (Figma Device Shell, desktop only) */}
          {isPhone && (
            <div className="hidden md:block" aria-hidden="true">
              {/* Left Rail: Action Button + Volume Up + Volume Down */}
              <div className="absolute -left-[3.5px] top-[108px] h-7 w-[3.5px] rounded-l-[2px] bg-gradient-to-b from-[#A1A1AA] via-[#5E5E66] to-[#3A3A40] shadow-xs ring-1 ring-black/25" />
              <div className="absolute -left-[3.5px] top-[154px] h-12 w-[3.5px] rounded-l-[2px] bg-gradient-to-b from-[#A1A1AA] via-[#5E5E66] to-[#3A3A40] shadow-xs ring-1 ring-black/25" />
              <div className="absolute -left-[3.5px] top-[214px] h-12 w-[3.5px] rounded-l-[2px] bg-gradient-to-b from-[#A1A1AA] via-[#5E5E66] to-[#3A3A40] shadow-xs ring-1 ring-black/25" />
              {/* Right Rail: Power Side Key + Camera Control Key */}
              <div className="absolute -right-[3.5px] top-[178px] h-[72px] w-[3.5px] rounded-r-[2px] bg-gradient-to-b from-[#A1A1AA] via-[#5E5E66] to-[#3A3A40] shadow-xs ring-1 ring-black/25" />
              <div className="absolute -right-[2.5px] top-[506px] h-14 w-[2.5px] rounded-r-[2px] bg-gradient-to-b from-[#71717A] via-[#3F3F46] to-[#52525B] ring-1 ring-black/30" />
            </div>
          )}

          {/* Outer Titanium Chassis Container (0px bezel/border on mobile < 768px) */}
          <div
            data-testid={isPhone ? "phone-bezel-frame" : "fullscreen-mobile-container"}
            className={`relative flex h-dvh w-full flex-col overflow-hidden ${screenBg} ${
              isPhone
                ? "md:h-[min(816px,calc(100dvh-4.75rem))] md:w-[408px] md:rounded-[56px] md:bg-gradient-to-br md:from-[#92929A] md:via-[#4E4E56] md:to-[#6C6C74] md:p-[3.5px] md:shadow-[0_32px_64px_-16px_rgba(24,24,27,0.38),0_10px_24px_-8px_rgba(24,24,27,0.22),inset_0_1px_1px_rgba(255,255,255,0.5)] md:ring-1 md:ring-black/25"
                : "md:h-full md:w-[600px] md:border-x md:border-zinc-300"
            }`}
          >
            {/* Titanium Antenna Band Details on Outer Chassis */}
            {isPhone && (
              <div className="pointer-events-none hidden md:block" aria-hidden="true">
                <div className="absolute left-0 top-[74px] h-[2px] w-[4px] bg-zinc-900/45" />
                <div className="absolute right-0 top-[74px] h-[2px] w-[4px] bg-zinc-900/45" />
                <div className="absolute bottom-[74px] left-0 h-[2px] w-[4px] bg-zinc-900/45" />
                <div className="absolute bottom-[74px] right-0 h-[2px] w-[4px] bg-zinc-900/45" />
              </div>
            )}

            {/* Inner Slim Matte Black OLED Display Bezel (Desktop Phone Preview only) */}
            <div
              className={`flex min-h-0 flex-1 flex-col overflow-hidden ${
                isPhone
                  ? "md:rounded-[52.5px] md:bg-[#09090B] md:p-[6px] md:shadow-[inset_0_0_0_1px_rgba(255,255,255,0.08)]"
                  : ""
              }`}
            >
              {/* Concentric Continuous OLED Glass Viewport */}
              <div
                className={`flex min-h-0 flex-1 flex-col overflow-hidden ${screenBg} text-zinc-900 ${
                  isPhone ? "md:rounded-[46.5px]" : ""
                }`}
              >
                {/* iPhone 18 Pro Status Bar & Compact Dynamic Island */}
                {isPhone && (
                  <div
                    className={`hidden h-10 shrink-0 items-center justify-between px-7 pt-2 ${screenBg} text-zinc-900 select-none md:flex`}
                  >
                    <span className="w-10 text-left text-[12px] font-semibold tracking-tight">
                      9:41
                    </span>

                    <div className="relative flex h-[24px] w-[90px] items-center justify-between rounded-full bg-[#09090B] px-2.5 shadow-[inset_0_0_0_0.5px_rgba(255,255,255,0.12)]">
                      <span className="h-[2px] w-7 rounded-full bg-zinc-800/90" />
                      <span className="flex h-3.5 w-3.5 items-center justify-center rounded-full bg-[#13151D] ring-1 ring-white/10">
                        <span className="h-1.5 w-1.5 rounded-full bg-[#243B64] shadow-[0_0_2px_rgba(96,165,250,0.45)]" />
                      </span>
                    </div>

                    <div className="flex w-12 items-center justify-end gap-1.5 text-zinc-900">
                      <span className="flex items-end gap-[1.5px]" aria-hidden="true">
                        <span className="h-[4px] w-[2px] rounded-full bg-zinc-900" />
                        <span className="h-[6px] w-[2px] rounded-full bg-zinc-900" />
                        <span className="h-[8px] w-[2px] rounded-full bg-zinc-900" />
                        <span className="h-[10px] w-[2px] rounded-full bg-zinc-900" />
                      </span>
                      <Wifi className="h-3 w-3 stroke-[2.3]" />
                      {/* Authentic iOS Battery Icon */}
                      <span className="inline-flex items-center" aria-hidden="true">
                        <span className="flex h-[10px] w-[19px] items-center rounded-[3px] border border-zinc-900/75 p-[1.5px]">
                          <span className="h-full w-[82%] rounded-[1.5px] bg-zinc-900" />
                        </span>
                        <span className="ml-[1px] h-[4px] w-[1.5px] rounded-r-full bg-zinc-900/75" />
                      </span>
                    </div>
                  </div>
                )}

                {header}

                <main
                  ref={scrollContainerRef}
                  className="mobile-scroll flex-1 overflow-y-auto overscroll-contain px-4 pb-5 pt-3"
                >
                  {children}
                </main>

                {bottomNav}

                {/* iPhone Pro Bottom Safe-Area Home Indicator */}
                {isPhone && (
                  <div
                    className={`hidden h-4 shrink-0 items-center justify-center bg-white md:flex`}
                  >
                    <div className="h-[4px] w-[122px] rounded-full bg-zinc-900/25" />
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
