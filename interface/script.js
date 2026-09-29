const form = document.querySelector("#estimation-form");
const submitButton = document.querySelector("#submit-button");
const buttonLabel = document.querySelector(".button-label");
const formError = document.querySelector("#form-error");
const resultStatus = document.querySelector("#result-status");
const priceValue = document.querySelector("#price-value");
const priceCurrency = document.querySelector("#price-currency");

const priceFormatter = new Intl.NumberFormat("fr-FR", {
  maximumFractionDigits: 2,
});

function showError(message) {
  formError.textContent = message;
  formError.hidden = false;
}

function clearError() {
  formError.textContent = "";
  formError.hidden = true;
}

function setLoading(isLoading) {
  submitButton.disabled = isLoading;
  form.setAttribute("aria-busy", String(isLoading));
  buttonLabel.textContent = isLoading ? "Estimation en cours…" : "Estimer le prix";
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  clearError();

  if (!form.reportValidity()) {
    showError("Vérifiez les champs obligatoires et les valeurs numériques saisies.");
    return;
  }

  const data = {
    marque: form.elements.marque.value.trim(),
    titre: form.elements.titre.value.trim(),
    processeur: form.elements.processeur.value.trim(),
    generation: form.elements.generation.value.trim(),
    ram_go: form.elements.ram_go.valueAsNumber,
    stockage_ssd: form.elements.stockage_ssd.valueAsNumber,
    stockage_hdd: form.elements.stockage_hdd.valueAsNumber,
    carte_graphique: form.elements.carte_graphique.value.trim(),
    ecran: form.elements.ecran.value.trim(),
    etat: form.elements.etat.value,
  };

  if (Object.values(data).some((value) => value === "" || (typeof value === "number" && !Number.isFinite(value)))) {
    showError("Certains champs sont vides ou contiennent une valeur invalide.");
    return;
  }

  setLoading(true);
  resultStatus.textContent = "Calcul de l'estimation…";
  priceValue.textContent = "—";
  priceCurrency.textContent = "FCFA";

  try {
    const response = await fetch("/predict", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(data),
    });

    let result;
    try {
      result = await response.json();
    } catch {
      resultStatus.textContent = "Estimation indisponible";
      showError("La réponse du service est inattendue. Réessayez dans un instant.");
      return;
    }

    if (!response.ok) {
      resultStatus.textContent = "Estimation indisponible";
      if (response.status === 422) {
        showError("Certaines caractéristiques ne sont pas valides. Vérifiez les valeurs saisies.");
      } else if (response.status >= 500) {
        showError("Le service rencontre un problème. Réessayez un peu plus tard.");
      } else {
        showError("La demande n'a pas pu être traitée. Vérifiez les informations et réessayez.");
      }
      return;
    }

    if (typeof result?.prix_estime !== "number" || !Number.isFinite(result.prix_estime)) {
      resultStatus.textContent = "Estimation indisponible";
      showError("Le service a renvoyé un résultat inattendu. Réessayez dans un instant.");
      return;
    }

    priceValue.textContent = priceFormatter.format(result.prix_estime);
    priceCurrency.textContent = typeof result.devise === "string" && result.devise.trim()
      ? result.devise
      : "FCFA";
    resultStatus.textContent = "Estimation indicative";
  } catch {
    resultStatus.textContent = "Estimation indisponible";
    showError("Impossible de joindre le service d'estimation. Vérifiez votre connexion puis réessayez.");
  } finally {
    setLoading(false);
  }
});
