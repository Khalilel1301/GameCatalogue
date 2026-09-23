const state = {
  page: 1,
  hasNext: false,
  loading: false,
  favorites: [],
  filters: {
    search: "",
    genre: "",
    platform: "",
    saga: "",
    ordering: "-rating"
  }
};

const $ = (selector) =>
  document.querySelector(selector);


// ==========================================================
// DOM SAFE
// ==========================================================

function on(selector, event, handler) {
  const element = $(selector);

  if (!element) {
    return;
  }

  element.addEventListener(
    event,
    handler
  );
}


// ==========================================================
// FAVORITES
// ==========================================================

async function loadFavoritesFromServer() {
  try {
    const data = await fetchJson(
      "/api/favorites"
    );

    state.favorites =
      Array.isArray(
        data.favorites
      )
        ? data.favorites
        : [];

  } catch (error) {
    console.error(
      "Erreur favoris :",
      error
    );

    state.favorites = [];
  }

  updateFavoriteCount();
  renderFavorites();
}


function isFavorite(id) {
  return state.favorites.some(
    (game) =>
      String(game.id)
      === String(id)
  );
}


async function addFavorite(game) {
  const favorite = {
    id: game.id,
    name: game.name,
    slug: game.slug || "",
    image:
      game.background_image
      || "",
    background_image:
      game.background_image
      || "",
    rating: game.rating,
    released: game.released,
    genres: game.genres || []
  };

  const data =
    await fetchJson(
      "/api/favorites",
      {
        method: "POST",
        headers: {
          "Content-Type":
            "application/json"
        },
        body:
          JSON.stringify(
            favorite
          )
      }
    );

  state.favorites =
    Array.isArray(
      data.favorites
    )
      ? data.favorites
      : state.favorites;

  updateFavoriteCount();
  renderFavorites();
  refreshFavoriteButtons(
    game.id
  );
}


async function removeFavorite(
  gameId
) {
  const data =
    await fetchJson(
      `/api/favorites/${encodeURIComponent(
        gameId
      )}`,
      {
        method: "DELETE"
      }
    );

  state.favorites =
    Array.isArray(
      data.favorites
    )
      ? data.favorites
      : state.favorites.filter(
          (item) =>
            String(item.id)
            !== String(gameId)
        );

  updateFavoriteCount();
  renderFavorites();
  refreshFavoriteButtons(
    gameId
  );
}


async function toggleFavorite(game) {
  try {
    if (isFavorite(game.id)) {
      await removeFavorite(
        game.id
      );
    } else {
      await addFavorite(
        game
      );
    }
  } catch (error) {
    console.error(
      "Erreur favori :",
      error
    );

    const status =
      $("#favoritesStatus");

    if (status) {
      setStatus(
        status,
        error.message,
        true
      );
    }
  }
}


function updateFavoriteCount() {
  const counter =
    $("#favoriteCount");

  if (!counter) {
    return;
  }

  counter.textContent =
    String(
      state.favorites.length
    );
}


function refreshFavoriteButtons(
  id
) {
  document
    .querySelectorAll(
      `[data-favorite-id="${CSS.escape(
        String(id)
      )}"]`
    )
    .forEach(
      (button) => {
        const active =
          isFavorite(id);

        button.classList.toggle(
          "active",
          active
        );

        button.textContent =
          active
            ? "♥"
            : "♡";

        button.setAttribute(
          "aria-label",
          active
            ? "Retirer des favoris"
            : "Ajouter aux favoris"
        );
      }
    );
}


// ==========================================================
// UTILITIES
// ==========================================================

function escapeUrl(value) {
  if (!value) {
    return "";
  }

  try {
    const url =
      new URL(value);

    return [
      "http:",
      "https:"
    ].includes(
      url.protocol
    )
      ? url.href
      : "";

  } catch {
    return "";
  }
}


function formatRating(value) {
  return typeof value === "number"
    ? `⭐ ${value.toFixed(1)}`
    : "⭐ Information non disponible";
}


function formatDate(value) {
  return value
    || "Information non disponible";
}


function fallbackImage() {
  const svg = `
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="800"
      height="500"
      viewBox="0 0 800 500"
    >
      <rect
        width="100%"
        height="100%"
        fill="#171c2c"
      />
      <text
        x="50%"
        y="50%"
        fill="#a7aec3"
        text-anchor="middle"
        dominant-baseline="middle"
        font-family="sans-serif"
        font-size="28"
      >
        Image non disponible
      </text>
    </svg>
  `;

  return (
    "data:image/svg+xml;charset=UTF-8,"
    + encodeURIComponent(
      svg
    )
  );
}


function metaItem(text) {
  const span =
    document.createElement(
      "span"
    );

  span.textContent =
    text;

  return span;
}


function setStatus(
  element,
  message,
  error = false
) {
  if (!element) {
    return;
  }

  element.textContent =
    message;

  element.classList.toggle(
    "error",
    Boolean(error)
  );
}


// ==========================================================
// API
// ==========================================================

async function fetchJson(
  url,
  options = {}
) {
  const response =
    await fetch(
      url,
      options
    );

  if (!response.ok) {

    let message =
      `Erreur HTTP ${response.status}`;

    try {
      const data =
        await response.json();

      if (data.error) {
        message =
          data.error;
      }

    } catch {
      // Rien à faire.
    }

    throw new Error(
      message
    );
  }

  return response.json();
}


// ==========================================================
// GAME CARD
// ==========================================================

function gameCard(game) {
  const article =
    document.createElement(
      "article"
    );

  article.className =
    "game-card";


  const clickArea =
    document.createElement(
      "button"
    );

  clickArea.type =
    "button";

  clickArea.className =
    "card-click-area";


  const imageWrap =
    document.createElement(
      "div"
    );

  imageWrap.className =
    "game-image-wrap";


  const image =
    document.createElement(
      "img"
    );

  image.className =
    "game-image";

  image.src =
    escapeUrl(
      game.background_image
    )
    || fallbackImage();

  image.alt =
    `${game.name || "Jeu"} — couverture`;

  image.loading =
    "lazy";

  image.addEventListener(
    "error",
    () => {
      image.src =
        fallbackImage();
    }
  );


  const favorite =
    document.createElement(
      "button"
    );

  favorite.type =
    "button";

  favorite.className =
    `favorite-button ${
      isFavorite(game.id)
        ? "active"
        : ""
    }`;

  favorite.dataset.favoriteId =
    String(game.id);

  favorite.textContent =
    isFavorite(game.id)
      ? "♥"
      : "♡";

  favorite.setAttribute(
    "aria-label",
    isFavorite(game.id)
      ? "Retirer des favoris"
      : "Ajouter aux favoris"
  );

  favorite.addEventListener(
    "click",
    (event) => {
      event.preventDefault();
      event.stopPropagation();

      toggleFavorite(
        game
      );
    }
  );


  imageWrap.append(
    image
  );

  clickArea.append(
    imageWrap
  );


  const body =
    document.createElement(
      "div"
    );

  body.className =
    "game-body";


  const title =
    document.createElement(
      "h3"
    );

  title.className =
    "game-title";

  title.textContent =
    game.name
    || "Information non disponible";


  const meta =
    document.createElement(
      "div"
    );

  meta.className =
    "game-meta";

  meta.append(
    metaItem(
      formatRating(
        game.rating
      )
    ),
    metaItem(
      `📅 ${formatDate(
        game.released
      )}`
    )
  );


  const tags =
    document.createElement(
      "div"
    );

  tags.className =
    "game-tags";


  (
    game.genres
    || []
  )
    .slice(0, 3)
    .forEach(
      (genre) => {
        const tag =
          document.createElement(
            "span"
          );

        tag.className =
          "tag";

        tag.textContent =
          genre.name
          || "Information non disponible";

        tags.append(tag);
      }
    );


  body.append(
    title,
    meta,
    tags
  );

  clickArea.append(
    body
  );

  article.append(
    clickArea,
    favorite
  );


  clickArea.addEventListener(
    "click",
    () => {
      openGame(
        game.id
      );
    }
  );


  return article;
}


// ==========================================================
// CATALOGUE URL
// ==========================================================

function buildGamesUrl(
  page = 1
) {
  const params =
    new URLSearchParams();

  params.set(
    "page",
    String(page)
  );

  params.set(
    "page_size",
    "20"
  );

  Object.entries(
    state.filters
  ).forEach(
    ([key, value]) => {

      if (
        value === undefined
        || value === null
      ) {
        return;
      }

      if (
        String(value).trim()
        === ""
      ) {
        return;
      }

      params.set(
        key,
        String(value)
      );
    }
  );

  return (
    `/api/games?${params.toString()}`
  );
}


// ==========================================================
// LOAD GAMES
// ==========================================================

async function loadGames({
  reset = false
} = {}) {

  if (state.loading) {
    return;
  }

  state.loading =
    true;

  const grid =
    $("#gamesGrid");

  const status =
    $("#catalogStatus");

  const loadMore =
    $("#loadMore");


  if (reset) {
    state.page =
      1;

    if (grid) {
      grid.replaceChildren();
    }
  }


  setStatus(
    status,
    "Chargement des jeux..."
  );


  if (loadMore) {
    loadMore.disabled =
      true;
  }


  try {

    const data =
      await fetchJson(
        buildGamesUrl(
          state.page
        )
      );


    if (!grid) {
      return;
    }


    if (
      reset
      && !data.results?.length
    ) {

      setStatus(
        status,
        "Aucun jeu ne correspond à ces critères."
      );

    } else {

      setStatus(
        status,
        `${data.count ?? data.results.length} résultat(s) trouvé(s).`
      );
    }


    (
      data.results
      || []
    ).forEach(
      (game) => {
        grid.append(
          gameCard(
            game
          )
        );
      }
    );


    state.hasNext =
      Boolean(
        data.next
      );


    if (loadMore) {
      loadMore.classList.toggle(
        "hidden",
        !state.hasNext
      );
    }

  } catch (error) {

    console.error(
      "Erreur catalogue :",
      error
    );

    setStatus(
      status,
      error.message,
      true
    );

    if (loadMore) {
      loadMore.classList.add(
        "hidden"
      );
    }

  } finally {

    state.loading =
      false;

    if (loadMore) {
      loadMore.disabled =
        false;
    }
  }
}


// ==========================================================
// SEARCH DEBOUNCE
// ==========================================================

let searchTimer;

function debounceCatalogSearch() {

  clearTimeout(
    searchTimer
  );

  searchTimer =
    setTimeout(
      () => {

        const input =
          $("#catalogSearch");

        state.filters.search =
          input
            ? input.value.trim()
            : "";

        loadGames({
          reset: true
        });

      },
      450
    );
}


// ==========================================================
// SAGA FILTER
// ==========================================================

function ensureSagaFilter() {

  if (
    $("#sagaFilter")
  ) {
    return;
  }


  const platform =
    $("#platformFilter");

  if (!platform) {
    return;
  }


  const label =
    document.createElement(
      "label"
    );

  label.className =
    "filter-group";


  const span =
    document.createElement(
      "span"
    );

  span.textContent =
    "Saga";


  const input =
    document.createElement(
      "input"
    );

  input.type =
    "text";

  input.id =
    "sagaFilter";

  input.placeholder =
    "Ex. Resident Evil";

  input.autocomplete =
    "off";


  label.append(
    span,
    input
  );


  const parent =
    platform.parentElement;


  if (parent) {

    parent.parentNode.insertBefore(
      label,
      parent.nextSibling
    );

  } else {

    platform.parentNode.append(
      label
    );
  }


  input.addEventListener(
    "input",
    () => {

      clearTimeout(
        searchTimer
      );

      state.filters.saga =
        input.value.trim();

      loadGames({
        reset: true
      });
    }
  );
}


// ==========================================================
// MODAL
// ==========================================================

async function openGame(
  gameId
) {
  const modal =
    $("#gameModal");

  const content =
    $("#modalContent");

  if (!modal || !content) {
    return;
  }


  modal.classList.remove(
    "hidden"
  );

  document.body.style.overflow =
    "hidden";

  content.replaceChildren();


  const loading =
    document.createElement(
      "div"
    );

  loading.className =
    "modal-section";

  loading.textContent =
    "Chargement de la fiche...";

  content.append(
    loading
  );


  try {

    const [
      game,
      screenshots
    ] =
      await Promise.all([
        fetchJson(
          `/api/games/${encodeURIComponent(
            gameId
          )}`
        ),

        fetchJson(
          `/api/games/${encodeURIComponent(
            gameId
          )}/screenshots`
        )
      ]);


    let trailer =
      null;


    try {

      const trailerData =
        await fetchJson(
          `/api/trailer?game=${encodeURIComponent(
            game.name
          )}`
        );

      trailer =
        trailerData.trailer
        || null;

    } catch (error) {

      console.warn(
        "Trailer indisponible :",
        error
      );
    }


    renderModal(
      game,
      screenshots.results || [],
      trailer
    );

  } catch (error) {

    content.replaceChildren();

    const section =
      document.createElement(
        "div"
      );

    section.className =
      "modal-section";

    section.textContent =
      error.message;

    content.append(
      section
    );
  }
}


function renderModal(
  game,
  screenshots,
  trailer
) {
  const content =
    $("#modalContent");

  if (!content) {
    return;
  }


  content.replaceChildren();


  // --------------------------------------------------------
  // HERO
  // --------------------------------------------------------

  const hero =
    document.createElement(
      "section"
    );

  hero.className =
    "modal-hero";


  const background =
    escapeUrl(
      game.background_image
    );


  if (background) {
    hero.style.backgroundImage =
      `url("${background.replaceAll(
        '"',
        '\\"'
      )}")`;
  }


  const heroContent =
    document.createElement(
      "div"
    );

  heroContent.className =
    "modal-hero-content";


  const eyebrow =
    document.createElement(
      "span"
    );

  eyebrow.className =
    "eyebrow";

  eyebrow.textContent =
    "FICHE DU JEU";


  const title =
    document.createElement(
      "h2"
    );

  title.id =
    "modalTitle";

  title.textContent =
    game.name
    || "Information non disponible";


  const meta =
    document.createElement(
      "div"
    );

  meta.className =
    "game-meta";

  meta.append(
    metaItem(
      formatRating(
        game.rating
      )
    ),

    metaItem(
      `📅 ${formatDate(
        game.released
      )}`
    ),

    metaItem(
      game.metacritic != null
        ? `Metacritic ${game.metacritic}`
        : "Metacritic : Information non disponible"
    )
  );


  heroContent.append(
    eyebrow,
    title,
    meta
  );

  hero.append(
    heroContent
  );


  // --------------------------------------------------------
  // INFORMATIONS
  // --------------------------------------------------------

  const info =
    document.createElement(
      "section"
    );

  info.className =
    "modal-section";


  const description =
    document.createElement(
      "p"
    );

  description.className =
    "modal-description";

  description.textContent =
    game.description
    || "Information non disponible.";


  const infoList =
    document.createElement(
      "div"
    );

  infoList.className =
    "info-list";


  const rows = [
    [
      "Genres",
      (
        game.genres
        || []
      ).map(
        (item) => item.name
      )
    ],

    [
      "Plateformes",
      (
        game.platforms
        || []
      ).map(
        (item) => item.name
      )
    ],

    [
      "Développeurs",
      (
        game.developers
        || []
      ).map(
        (item) => item.name
      )
    ],

    [
      "Éditeurs",
      (
        game.publishers
        || []
      ).map(
        (item) => item.name
      )
    ]
  ];


  rows.forEach(
    ([label, values]) => {

      const wrapper =
        document.createElement(
          "div"
        );

      wrapper.className =
        "game-tags";


      const strong =
        document.createElement(
          "strong"
        );

      strong.textContent =
        `${label} :`;


      wrapper.append(
        strong
      );


      const cleanValues =
        values
          .filter(Boolean)
          .slice(
            0,
            12
          );


      if (!cleanValues.length) {
        cleanValues.push(
          "Information non disponible"
        );
      }


      cleanValues.forEach(
        (value) => {

          const tag =
            document.createElement(
              "span"
            );

          tag.className =
            "tag";

          tag.textContent =
            value;

          wrapper.append(
            tag
          );
        }
      );


      infoList.append(
        wrapper
      );
    }
  );


  info.append(
    description,
    infoList
  );


  if (game.website) {

    const website =
      escapeUrl(
        game.website
      );

    if (website) {

      const link =
        document.createElement(
          "a"
        );

      link.className =
        "external-link";

      link.href =
        website;

      link.target =
        "_blank";

      link.rel =
        "noopener noreferrer";

      link.textContent =
        "Site officiel du jeu ↗";

      info.append(
        document.createElement(
          "br"
        ),
        link
      );
    }
  }


  // --------------------------------------------------------
  // SCREENSHOTS
  // --------------------------------------------------------

  const screenshotSection =
    document.createElement(
      "section"
    );

  screenshotSection.className =
    "modal-section";


  const screenshotTitle =
    document.createElement(
      "h3"
    );

  screenshotTitle.textContent =
    "Screenshots";


  screenshotSection.append(
    screenshotTitle
  );


  if (screenshots.length) {

    const screenshotGrid =
      document.createElement(
        "div"
      );

    screenshotGrid.className =
      "screenshot-grid";


    screenshots.forEach(
      (shot) => {

        const img =
          document.createElement(
            "img"
          );

        img.src =
          escapeUrl(
            shot.image
          )
          || fallbackImage();

        img.alt =
          `${game.name} — screenshot`;

        img.loading =
          "lazy";


        img.addEventListener(
          "error",
          () => {
            img.src =
              fallbackImage();
          }
        );


        screenshotGrid.append(
          img
        );
      }
    );


    screenshotSection.append(
      screenshotGrid
    );

  } else {

    const p =
      document.createElement(
        "p"
      );

    p.className =
      "modal-description";

    p.textContent =
      "Information non disponible";

    screenshotSection.append(
      p
    );
  }


  // --------------------------------------------------------
  // TRAILER
  // --------------------------------------------------------

  const trailerSection =
    document.createElement(
      "section"
    );

  trailerSection.className =
    "modal-section";


  const trailerTitle =
    document.createElement(
      "h3"
    );

  trailerTitle.textContent =
    "Trailer YouTube";


  trailerSection.append(
    trailerTitle
  );


  if (
    trailer
    && trailer.video_id
  ) {

    const iframe =
      document.createElement(
        "iframe"
      );

    iframe.className =
      "trailer";

    iframe.src =
      escapeUrl(
        trailer.embed_url
      );

    iframe.title =
      trailer.title
      || "Trailer YouTube";

    iframe.loading =
      "lazy";

    iframe.allow =
      "accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share";

    iframe.allowFullscreen =
      true;


    trailerSection.append(
      iframe
    );


    const channel =
      document.createElement(
        "p"
      );

    channel.className =
      "modal-description";

    channel.textContent =
      `Vidéo : ${
        trailer.title
        || "Information non disponible"
      } — chaîne : ${
        trailer.channel
        || "Information non disponible"
      }`;


    trailerSection.append(
      channel
    );

  } else {

    const p =
      document.createElement(
        "p"
      );

    p.className =
      "modal-description";

    p.textContent =
      "Trailer : Information non disponible";

    trailerSection.append(
      p
    );
  }


  content.append(
    hero,
    info,
    screenshotSection,
    trailerSection
  );
}


function closeModal() {
  const modal =
    $("#gameModal");

  if (!modal) {
    return;
  }

  modal.classList.add(
    "hidden"
  );

  document.body.style.overflow =
    "";
}


// ==========================================================
// FAVORITES PAGE
// ==========================================================

function renderFavorites() {
  const grid =
    $("#favoritesGrid");

  const status =
    $("#favoritesStatus");

  if (!grid) {
    return;
  }


  grid.replaceChildren();


  if (
    !state.favorites.length
  ) {

    setStatus(
      status,
      "Aucun favori pour le moment."
    );

    return;
  }


  setStatus(
    status,
    `${state.favorites.length} favori(s).`
  );


  state.favorites.forEach(
    (game) => {

      const normalizedGame =
        {
          ...game,
          background_image:
            game.background_image
            || game.image
            || ""
        };

      grid.append(
        gameCard(
          normalizedGame
        )
      );
    }
  );
}


// ==========================================================
// GAMEBOT
// ==========================================================

function appendChat(
  text,
  type = "bot"
) {
  const container =
    $("#chatMessages");

  if (!container) {
    return null;
  }


  const message =
    document.createElement(
      "div"
    );

  message.className =
    `chat-message ${
      type === "user"
        ? "user-message"
        : "bot-message"
    }`;


  const strong =
    document.createElement(
      "strong"
    );

  strong.textContent =
    type === "user"
      ? "Vous"
      : "GameBot";


  const paragraph =
    document.createElement(
      "p"
    );

  paragraph.textContent =
    text;


  message.append(
    strong,
    paragraph
  );

  container.append(
    message
  );


  container.scrollTop =
    container.scrollHeight;


  return message;
}


function renderCriteria(
  criteria
) {
  const box =
    $("#criteriaBox");

  if (!box) {
    return;
  }


  box.replaceChildren();

  box.classList.remove(
    "hidden"
  );


  const title =
    document.createElement(
      "strong"
    );

  title.textContent =
    "Critères compris par GameBot";


  const list =
    document.createElement(
      "div"
    );

  list.className =
    "criteria-list";


  const values = [];


  if (
    criteria.search
  ) {
    values.push(
      `Recherche : ${criteria.search}`
    );
  }


  (
    criteria.genres
    || []
  ).forEach(
    (value) => {
      values.push(
        `Genre : ${value}`
      );
    }
  );


  (
    criteria.platforms
    || []
  ).forEach(
    (value) => {
      values.push(
        `Plateforme : ${value}`
      );
    }
  );


  (
    criteria.tags
    || []
  ).forEach(
    (value) => {
      values.push(
        `Tag : ${value}`
      );
    }
  );


  if (
    criteria.released_after
  ) {
    values.push(
      `Après : ${criteria.released_after}`
    );
  }


  if (
    criteria.released_before
  ) {
    values.push(
      `Avant : ${criteria.released_before}`
    );
  }


  if (
    criteria.ordering
  ) {
    values.push(
      `Tri : ${criteria.ordering}`
    );
  }


  if (!values.length) {
    values.push(
      "Aucun critère précis"
    );
  }


  values.forEach(
    (value) => {

      const tag =
        document.createElement(
          "span"
        );

      tag.className =
        "tag";

      tag.textContent =
        value;

      list.append(
        tag
      );
    }
  );


  box.append(
    title,
    list
  );
}


async function handleRecommendation(
  event
) {
  event.preventDefault();


  const input =
    $("#recommendInput");

  if (!input) {
    return;
  }


  const message =
    input.value.trim();


  if (!message) {
    return;
  }


  appendChat(
    message,
    "user"
  );


  input.value =
    "";


  const pending =
    appendChat(
      "Je comprends ta recherche et je consulte le catalogue..."
    );


  if (!pending) {
    return;
  }


  try {

    const data =
      await fetchJson(
        "/api/recommend",
        {
          method: "POST",
          headers: {
            "Content-Type":
              "application/json"
          },
          body:
            JSON.stringify({
              message
            })
        }
      );


    const paragraph =
      pending.querySelector(
        "p"
      );

    if (paragraph) {
      paragraph.textContent =
        data.message
        || "Recherche terminée.";
    }


    pending.classList.remove(
      "error"
    );


    renderCriteria(
      data.criteria
      || {}
    );


    const grid =
      $("#recommendGrid");

    if (!grid) {
      return;
    }


    grid.replaceChildren();


    if (
      !Array.isArray(
        data.results
      )
      || !data.results.length
    ) {

      const status =
        document.createElement(
          "p"
        );

      status.className =
        "status-message";

      status.textContent =
        "Aucun résultat RAWG pour ces critères.";

      grid.append(
        status
      );

      return;
    }


    data.results.forEach(
      (game) => {
        grid.append(
          gameCard(
            game
          )
        );
      }
    );

  } catch (error) {

    const paragraph =
      pending.querySelector(
        "p"
      );

    if (paragraph) {
      paragraph.textContent =
        error.message;
    }

    pending.classList.add(
      "error"
    );
  }
}


// ==========================================================
// THEME
// ==========================================================

function initTheme() {
  const saved =
    localStorage.getItem(
      "gamecatalogue:theme"
    );


  if (
    saved === "light"
  ) {
    document.body.classList.add(
      "light"
    );
  }


  const toggle =
    $("#themeToggle");

  if (toggle) {
    toggle.textContent =
      document.body.classList.contains(
        "light"
      )
        ? "🌙"
        : "☀️";
  }
}


// ==========================================================
// EVENTS
// ==========================================================

on(
  "#heroSearchForm",
  "submit",
  (event) => {

    event.preventDefault();

    const heroSearch =
      $("#heroSearch");

    const catalogSearch =
      $("#catalogSearch");

    const value =
      heroSearch
        ? heroSearch.value.trim()
        : "";


    if (catalogSearch) {
      catalogSearch.value =
        value;
    }


    state.filters.search =
      value;


    const explore =
      $("#explore");

    if (explore) {
      explore.scrollIntoView({
        behavior:
          "smooth"
      });
    }


    loadGames({
      reset: true
    });
  }
);


on(
  "#catalogSearch",
  "input",
  debounceCatalogSearch
);


on(
  "#genreFilter",
  "change",
  () => {

    const element =
      $("#genreFilter");

    state.filters.genre =
      element
        ? element.value
        : "";

    loadGames({
      reset: true
    });
  }
);


on(
  "#platformFilter",
  "change",
  () => {

    const element =
      $("#platformFilter");

    state.filters.platform =
      element
        ? element.value
        : "";

    loadGames({
      reset: true
    });
  }
);


on(
  "#sortFilter",
  "change",
  () => {

    const element =
      $("#sortFilter");

    state.filters.ordering =
      element
        ? element.value
        : "-rating";

    loadGames({
      reset: true
    });
  }
);


on(
  "#clearFilters",
  "click",
  () => {

    state.filters = {
      search: "",
      genre: "",
      platform: "",
      saga: "",
      ordering: "-rating"
    };


    const catalogSearch =
      $("#catalogSearch");

    const genre =
      $("#genreFilter");

    const platform =
      $("#platformFilter");

    const saga =
      $("#sagaFilter");

    const sort =
      $("#sortFilter");


    if (catalogSearch) {
      catalogSearch.value =
        "";
    }

    if (genre) {
      genre.value =
        "";
    }

    if (platform) {
      platform.value =
        "";
    }

    if (saga) {
      saga.value =
        "";
    }

    if (sort) {
      sort.value =
        "-rating";
    }


    loadGames({
      reset: true
    });
  }
);


on(
  "#loadMore",
  "click",
  () => {

    if (!state.hasNext) {
      return;
    }

    state.page +=
      1;

    loadGames();
  }
);


on(
  "#recommendForm",
  "submit",
  handleRecommendation
);


on(
  "#closeModal",
  "click",
  closeModal
);


const modalOverlay =
  document.querySelector(
    "[data-close-modal]"
  );

if (modalOverlay) {
  modalOverlay.addEventListener(
    "click",
    closeModal
  );
}


document.addEventListener(
  "keydown",
  (event) => {

    if (
      event.key === "Escape"
    ) {

      const modal =
        $("#gameModal");

      if (
        modal
        && !modal.classList.contains(
          "hidden"
        )
      ) {
        closeModal();
      }
    }
  }
);


on(
  "#themeToggle",
  "click",
  () => {

    document.body.classList.toggle(
      "light"
    );


    const light =
      document.body.classList.contains(
        "light"
      );


    localStorage.setItem(
      "gamecatalogue:theme",
      light
        ? "light"
        : "dark"
    );


    const toggle =
      $("#themeToggle");

    if (toggle) {
      toggle.textContent =
        light
          ? "🌙"
          : "☀️";
    }
  }
);


on(
  "#mobileMenuButton",
  "click",
  () => {

    const nav =
      $("#mainNav");

    const button =
      $("#mobileMenuButton");


    if (!nav) {
      return;
    }


    const open =
      nav.classList.toggle(
        "open"
      );


    if (button) {
      button.setAttribute(
        "aria-expanded",
        String(open)
      );
    }
  }
);


document
  .querySelectorAll(
    "#mainNav a"
  )
  .forEach(
    (link) => {

      link.addEventListener(
        "click",
        () => {

          const nav =
            $("#mainNav");

          const button =
            $("#mobileMenuButton");


          if (nav) {
            nav.classList.remove(
              "open"
            );
          }

          if (button) {
            button.setAttribute(
              "aria-expanded",
              "false"
            );
          }
        }
      );
    }
  );


// ==========================================================
// INITIALISATION
// ==========================================================

ensureSagaFilter();
initTheme();
updateFavoriteCount();
renderFavorites();
loadFavoritesFromServer();

loadGames({
  reset: true
});