const workflow = [
  "Check in",
  "Work and link Zammad tickets",
  "Submit period",
  "Admin review",
  "Approval",
  "Payment and invoice",
];

export default function Home() {
  return (
    <main className="shell">
      <section className="intro">
        <p className="eyebrow">Technology Center Lanka</p>
        <h1>TCL WorkHub</h1>
        <p>
          Internal work-hours, verification, approval, payment, and invoice management.
        </p>
      </section>

      <section className="workflow" aria-label="MVP workflow">
        {workflow.map((item, index) => (
          <div className="step" key={item}>
            <span>{index + 1}</span>
            <p>{item}</p>
          </div>
        ))}
      </section>
    </main>
  );
}

