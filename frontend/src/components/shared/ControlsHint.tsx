/**
 * ControlsHint - Simple hint panel for keyboard shortcuts
 */

export function ControlsHint() {
  return (
    <div className="absolute bottom-4 left-4 px-3 py-2 bg-slate-800/90 backdrop-blur-sm border border-slate-700 rounded-lg text-xs text-slate-400">
      Click zone to select • Scroll to zoom • Middle-click drag to pan • Double-click to fit
    </div>
  );
}
