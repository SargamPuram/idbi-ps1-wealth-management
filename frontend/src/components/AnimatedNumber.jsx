import { useEffect, useRef, useState } from "react";

function formatINR(value, { decimals = 0, compact = false } = {}) {
  if (compact) {
    const abs = Math.abs(value);
    if (abs >= 1e7) return `${(value / 1e7).toFixed(2)} Cr`;
    if (abs >= 1e5) return `${(value / 1e5).toFixed(2)} L`;
    if (abs >= 1e3) return `${(value / 1e3).toFixed(1)} K`;
  }
  return value.toLocaleString("en-IN", {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
}

/** Animated, comma-formatted (Indian numbering) number counter, optionally prefixed with ₹. */
export default function AnimatedNumber({
  value = 0,
  prefix = "",
  suffix = "",
  duration = 900,
  decimals = 0,
  compact = false,
  className = "",
}) {
  const [display, setDisplay] = useState(0);
  const startRef = useRef(null);
  const fromRef = useRef(0);

  useEffect(() => {
    fromRef.current = display;
    startRef.current = null;
    const target = Number(value) || 0;
    let raf;

    function step(ts) {
      if (startRef.current === null) startRef.current = ts;
      const progress = Math.min((ts - startRef.current) / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      const current = fromRef.current + (target - fromRef.current) * eased;
      setDisplay(current);
      if (progress < 1) raf = requestAnimationFrame(step);
    }
    raf = requestAnimationFrame(step);
    return () => cancelAnimationFrame(raf);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [value]);

  return (
    <span className={className}>
      {prefix}
      {formatINR(display, { decimals, compact })}
      {suffix}
    </span>
  );
}

export { formatINR };
