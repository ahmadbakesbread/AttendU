export default function ActionButton({
  variant = "neutral",
  children,
  style,
  ...props
}) {
  const palette = {
    danger:  { border: "#f87171", text: "#f87171", hover: "rgba(248,113,113,0.12)" },
    success: { border: "#34d399", text: "#34d399", hover: "rgba(52,211,153,0.12)" },
    neutral: { border: "#9CA3AF", text: "#E5E7EB",  hover: "rgba(156,163,175,0.12)" },
  }[variant];

  const base = {
    padding: "6px 10px",
    borderRadius: 6,
    border: `1px solid ${palette.border}`,
    background: "transparent",
    color: palette.text,
    cursor: "pointer",
    transition: "background 120ms ease, transform 80ms ease",
    ...style,
  };

  return (
    <button
      {...props}
      style={base}
      onMouseEnter={(e) => (e.currentTarget.style.background = palette.hover)}
      onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
      onMouseDown={(e) => (e.currentTarget.style.transform = "translateY(1px)")}
      onMouseUp={(e) => (e.currentTarget.style.transform = "translateY(0)")}
    >
      {children}
    </button>
  );
}

export { default as ActionButton } from "./ActionButton.jsx";
