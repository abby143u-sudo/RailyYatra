export default function PublicDemoInternalPanel({ title, description, children, defaultOpen = false }) {
  return (
    <details className="public-demo-internal-panel" open={defaultOpen}>
      <summary>
        <span>
          <strong>{title}</strong>
          {description ? <small>{description}</small> : null}
        </span>
        <em>Open</em>
      </summary>
      <div className="public-demo-internal-panel__body">{children}</div>
    </details>
  );
}
