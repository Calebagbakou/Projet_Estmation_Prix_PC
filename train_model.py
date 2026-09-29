from pathlib import Path

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from normalization import (
    normalize_brand,
    normalize_condition,
    normalize_generation,
    normalize_gpu,
    normalize_processor,
    normalize_screen,
    normalize_title,
)

BASE_DIR = Path(__file__).resolve().parent
dataset_path = BASE_DIR / "pc_bj_v32.xlsx"
model_path = BASE_DIR / "modele.joblib"

features = [
    "marque",
    "titre",
    "processeur",
    "generation",
    "ram_go",
    "stockage_ssd",
    "stockage_hdd",
    "carte_graphique",
    "ecran",
    "etat",
]

raw_data = pd.read_excel(dataset_path)
data = raw_data.dropna(subset=features + ["prix_fcfa"]).copy()
data["marque"] = data["marque"].map(normalize_brand)
data["titre"] = data["titre"].map(normalize_title)
data["processeur"] = data["processeur"].map(normalize_processor)
data["generation"] = data["generation"].map(normalize_generation)
data["carte_graphique"] = data["carte_graphique"].map(normalize_gpu)
data["ecran"] = data["ecran"].map(normalize_screen)
data["etat"] = data["etat"].map(normalize_condition)

price_iqr = data["prix_fcfa"].quantile(0.75) - data["prix_fcfa"].quantile(0.25)
lower_bound = data["prix_fcfa"].quantile(0.25) - 1.5 * price_iqr
upper_bound = data["prix_fcfa"].quantile(0.75) + 1.5 * price_iqr
data = data[data["prix_fcfa"].between(lower_bound, upper_bound)]

X = data[features]
y = data["prix_fcfa"]

categorical_features = [
    "marque",
    "titre",
    "processeur",
    "generation",
    "carte_graphique",
    "ecran",
    "etat",
]
numerical_features = ["ram_go", "stockage_ssd", "stockage_hdd"]

preprocessor = ColumnTransformer(
    transformers=[
        ("num", StandardScaler(), numerical_features),
        (
            "cat",
            OneHotEncoder(handle_unknown="ignore", sparse_output=False),
            categorical_features,
        ),
    ]
)

pipeline = Pipeline(
    steps=[
        ("preprocessor", preprocessor),
        (
            "model",
            RandomForestRegressor(
                n_estimators=300,
                random_state=42,
                n_jobs=-1,
            ),
        ),
    ]
)

X_train, _, y_train, _ = train_test_split(
    X,
    y,
    test_size=0.15,
    random_state=42,
)
pipeline.fit(X_train, y_train)
joblib.dump(pipeline, model_path)
print(f"Pipeline sauvegarde : {model_path}")
print(f"Lignes utilisees : {len(X_train)}")
