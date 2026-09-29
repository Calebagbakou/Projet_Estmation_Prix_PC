from pathlib import Path
from typing import Any

import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, field_validator, model_validator

from normalization import (
    clean_text,
    normalize_brand,
    normalize_condition,
    normalize_generation,
    normalize_gpu,
    normalize_processor,
    normalize_screen,
    normalize_title,
)


app = FastAPI(
    title="Estimation du prix d'un PC",
    description="API pour estimer le prix d'un ordinateur portable",
    version="1.0.0",
)

MODEL_PATH = Path(__file__).parent / "modele.joblib"

try:
    model = joblib.load(MODEL_PATH)
except Exception as error:
    raise RuntimeError(f"Impossible de charger le modèle : {error}")


class PCFeatures(BaseModel):
    marque: str = Field(..., min_length=1, description="Marque du PC", examples=["Dell"])
    titre: str = Field(..., min_length=1, description="Nom ou modèle du PC", examples=["Dell Latitude 5520"])
    processeur: str = Field(..., min_length=1, description="Modèle du processeur", examples=["Intel Core i5-1135G7"])
    generation: str = Field(..., min_length=1, description="Génération du processeur", examples=["11eme"])
    ram_go: float = Field(..., gt=0, description="RAM en Go, par exemple 8 ou 16", examples=[16])
    stockage_ssd: float = Field(..., ge=0, description="Stockage SSD en Go", examples=[512])
    stockage_hdd: float = Field(..., ge=0, description="Stockage HDD en Go, 0 si absent", examples=[0])
    carte_graphique: str = Field(..., min_length=1, description="Modèle de la carte graphique", examples=["Intel Iris Xe"])
    ecran: str = Field(..., min_length=1, description="Taille de l'écran", examples=["15.6 pouces"])
    etat: str = Field(..., min_length=1, description="État du PC", examples=["Neuf"])

    _normalize_brand = field_validator("marque", mode="before")(normalize_brand)
    _normalize_title = field_validator("titre", mode="before")(normalize_title)
    _normalize_processor = field_validator("processeur", mode="before")(normalize_processor)
    _normalize_generation = field_validator("generation", mode="before")(normalize_generation)
    _normalize_gpu = field_validator("carte_graphique", mode="before")(normalize_gpu)
    _normalize_screen = field_validator("ecran", mode="before")(normalize_screen)
    _normalize_condition = field_validator("etat", mode="before")(normalize_condition)

    @model_validator(mode="before")
    @classmethod
    def reject_missing_text(cls, values: Any) -> Any:
        text_fields = (
            "marque",
            "titre",
            "processeur",
            "generation",
            "carte_graphique",
            "ecran",
            "etat",
        )
        for field_name in text_fields:
            value = values.get(field_name) if isinstance(values, dict) else None
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"Le champ '{field_name}' est obligatoire.")
        return values

    @field_validator("marque", "titre", "processeur", "generation", "carte_graphique", "ecran", "etat")
    @classmethod
    def reject_empty_values(cls, value: str) -> str:
        if not clean_text(value):
            raise ValueError("Ce champ ne peut pas être vide.")
        return value

    model_config = {
        "json_schema_extra": {
            "example": {
                "marque": "Dell",
                "titre": "Dell Latitude 5520",
                "processeur": "Intel Core i5-1135G7",
                "generation": "11eme",
                "ram_go": 16,
                "stockage_ssd": 512,
                "stockage_hdd": 0,
                "carte_graphique": "Intel Iris Xe",
                "ecran": "15.6 pouces",
                "etat": "Neuf",
            }
        }
    }


@app.get("/")
def home() -> dict[str, str]:
    return {"message": "API d'estimation du prix du PC opérationnelle"}


@app.get("/health")
def health() -> dict[str, str]:
    status = "ok" if hasattr(model, "named_steps") else "model_incompatible"
    return {"status": status}


@app.post("/predict")
def predict_pc_price(pc: PCFeatures) -> dict[str, Any]:
    if not hasattr(model, "named_steps"):
        raise HTTPException(
            status_code=503,
            detail=(
                "Le fichier modele.joblib ne contient pas le pipeline complet. "
                "Réexécutez l'entraînement et sauvegardez preprocessor + modèle."
            ),
        )

    try:
        # Le pipeline attend les colonnes utilisées dans le notebook d'entraînement.
        features = pd.DataFrame([pc.model_dump()])

        prediction = model.predict(features)[0]

        return {
            "prix_estime": round(float(prediction), 2),
            "devise": "FCFA",
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur pendant la prédiction : {error}",
        )