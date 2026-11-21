function applyLanguage(language) {
  document.documentElement.lang = language;

  document.querySelectorAll("[data-en][data-nl]").forEach((element) => {
    element.textContent =
      language === "nl" ? element.dataset.nl : element.dataset.en;
  });

  document.querySelectorAll("[data-language]").forEach((button) => {
    button.setAttribute(
      "aria-pressed",
      String(button.dataset.language === language),
    );
  });
}

document.querySelectorAll("[data-language]").forEach((button) => {
  button.addEventListener("click", () => {
    applyLanguage(button.dataset.language);
    filterDirectory();
  });
});

const search = document.querySelector("#venue-search");
const sportFilter = document.querySelector("#sport-filter");
const cityFilter = document.querySelector("#city-filter");
const cards = [...document.querySelectorAll("[data-venue-card]")];
const count = document.querySelector("#listing-count");
const emptyResults = document.querySelector("#empty-results");

function filterDirectory() {
  if (!cards.length) return;

  const query = search?.value.trim().toLocaleLowerCase() ?? "";
  const sport = sportFilter?.value ?? "";
  const city = cityFilter?.value ?? "";
  let visible = 0;

  for (const card of cards) {
    const matches =
      (!query || card.dataset.search.includes(query)) &&
      (!sport || card.dataset.sports.split(" ").includes(sport)) &&
      (!city || card.dataset.city === city);
    card.hidden = !matches;
    if (matches) visible += 1;
  }

  if (count) {
    count.textContent = document.documentElement.lang === "nl"
      ? `${visible} ${visible === 1 ? "locatie" : "locaties"}`
      : `${visible} ${visible === 1 ? "listing" : "listings"}`;
  }
  if (emptyResults) emptyResults.hidden = visible > 0;
}

search?.addEventListener("input", filterDirectory);
sportFilter?.addEventListener("change", filterDirectory);
cityFilter?.addEventListener("change", filterDirectory);

applyLanguage("en");
filterDirectory();
