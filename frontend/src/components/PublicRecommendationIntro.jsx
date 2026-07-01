export default function PublicRecommendationIntro() {
  return (
    <section className="public-recommendation-intro" aria-label="RailYatra recommendation engine intro">
      <div>
        <p className="public-recommendation-intro__eyebrow">Recommendation engine</p>
        <h2>Ranked route options with transfer-safety signals</h2>
        <p>
          RailYatra compares route options and presents preview recommendations with confidence-style scoring, transfer context and clear safety warnings.
        </p>
      </div>

      <div className="public-recommendation-intro__signals">
        <article>
          <span>Score</span>
          <strong>Best-fit ranking</strong>
        </article>
        <article>
          <span>Transfer</span>
          <strong>Connection safety</strong>
        </article>
        <article>
          <span>Preview</span>
          <strong>No live booking yet</strong>
        </article>
      </div>
    </section>
  );
}
