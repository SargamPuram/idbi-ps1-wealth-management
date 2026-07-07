import "./Avatar.css";

/**
 * Dhanvi's avatar — a CSS-animated gradient orb (no external asset/Lottie
 * dependency, so it always renders even offline). Three states:
 * idle (gentle float+breathe), thinking (orbiting dots), speaking (pulse rings + waveform).
 */
export default function Avatar({ state = "idle" }) {
  return (
    <div className={`dhanvi-avatar dhanvi-avatar-${state}`}>
      <div className="avatar-particles">
        {Array.from({ length: 8 }).map((_, i) => (
          <span key={i} className={`particle particle-${i}`} />
        ))}
      </div>

      {state === "speaking" && (
        <>
          <span className="pulse-ring pulse-ring-1" />
          <span className="pulse-ring pulse-ring-2" />
        </>
      )}

      <div className="avatar-orb">
        <div className="avatar-orb-inner">
          <div className="avatar-face">
            <div className="avatar-eyes">
              <span className="eye" />
              <span className="eye" />
            </div>
            {state === "thinking" ? (
              <div className="avatar-thinking-dots">
                <span />
                <span />
                <span />
              </div>
            ) : (
              <div className={`avatar-mouth ${state === "speaking" ? "avatar-mouth-talk" : ""}`} />
            )}
          </div>
        </div>
        <div className="avatar-shine" />
      </div>

      {state === "speaking" && (
        <div className="avatar-waveform">
          {Array.from({ length: 5 }).map((_, i) => (
            <span key={i} className={`wave-bar wave-bar-${i}`} />
          ))}
        </div>
      )}
    </div>
  );
}
