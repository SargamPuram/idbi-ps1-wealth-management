export function LoadingBlock({ height = 120 }) {
  return <div className="shimmer" style={{ height, width: "100%" }} />;
}

export function ErrorBlock({ message }) {
  return (
    <div className="card" style={{ borderColor: "rgba(239,68,68,0.35)" }}>
      <strong style={{ color: "var(--red)" }}>Couldn't load this.</strong>
      <p style={{ color: "var(--text-secondary)", marginTop: 6, fontSize: 13 }}>{message}</p>
    </div>
  );
}
