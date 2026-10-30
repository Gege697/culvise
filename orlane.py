```python
import json
import os
from datetime import datetime

# ============================================================
# CONFIGURATION
# ============================================================

FICHIER_ARTICLES = "articles.json"
FICHIER_COMMANDES = "commandes.json"


# ============================================================
# BASE DE DONNÉES DES ARTICLES
# ============================================================

ARTICLES_PAR_DEFAUT = {
    "A001": {
        "nom": "Ordinateur portable",
        "prix": 350000,
        "stock": 10
    },
    "A002": {
        "nom": "Téléphone Samsung",
        "prix": 180000,
        "stock": 15
    },
    "A003": {
        "nom": "Casque Bluetooth",
        "prix": 25000,
        "stock": 20
    },
    "A004": {
        "nom": "Souris sans fil",
        "prix": 12000,
        "stock": 30
    },
    "A005": {
        "nom": "Clavier USB",
        "prix": 15000,
        "stock": 25
    },
    "A006": {
        "nom": "Disque SSD 500 Go",
        "prix": 45000,
        "stock": 12
    }
}


# ============================================================
# CHARGEMENT / SAUVEGARDE DES DONNÉES
# ============================================================

def charger_articles():
    """Charge les articles depuis le fichier JSON."""

    if not os.path.exists(FICHIER_ARTICLES):
        sauvegarder_articles(ARTICLES_PAR_DEFAUT)
        return ARTICLES_PAR_DEFAUT.copy()

    try:
        with open(FICHIER_ARTICLES, "r", encoding="utf-8") as fichier:
            return json.load(fichier)

    except (json.JSONDecodeError, FileNotFoundError):
        print("Erreur de lecture de la base de données.")
        print("La base par défaut sera utilisée.")

        sauvegarder_articles(ARTICLES_PAR_DEFAUT)
        return ARTICLES_PAR_DEFAUT.copy()


def sauvegarder_articles(articles):
    """Sauvegarde la base des articles."""

    with open(FICHIER_ARTICLES, "w", encoding="utf-8") as fichier:
        json.dump(
            articles,
            fichier,
            ensure_ascii=False,
            indent=4
        )


def charger_commandes():
    """Charge l'historique des commandes."""

    if not os.path.exists(FICHIER_COMMANDES):
        return []

    try:
        with open(FICHIER_COMMANDES, "r", encoding="utf-8") as fichier:
            return json.load(fichier)

    except json.JSONDecodeError:
        return []


def sauvegarder_commandes(commandes):
    """Sauvegarde l'historique des commandes."""

    with open(FICHIER_COMMANDES, "w", encoding="utf-8") as fichier:
        json.dump(
            commandes,
            fichier,
            ensure_ascii=False,
            indent=4
        )


# ============================================================
# AFFICHAGE DES ARTICLES
# ============================================================

def afficher_articles(articles):
    """Affiche tous les articles disponibles."""

    print("\n" + "=" * 75)
    print("                         STOCK DE LA BOUTIQUE")
    print("=" * 75)

    print(
        f"{'CODE':<10}"
        f"{'ARTICLE':<30}"
        f"{'PRIX':>15}"
        f"{'STOCK':>15}"
    )

    print("-" * 75)

    for code, article in articles.items():

        prix = f"{article['prix']:,} FCFA"

        print(
            f"{code:<10}"
            f"{article['nom']:<30}"
            f"{prix:>15}"
            f"{article['stock']:>15}"
        )

    print("=" * 75)


# ============================================================
# RECHERCHE D'UN ARTICLE
# ============================================================

def choisir_article(articles):
    """Demande à l'utilisateur le code de l'article."""

    while True:

        code = input(
            "\nEntrez le code de l'article "
            "(ou 'fin' pour terminer) : "
        ).upper().strip()

        if code == "FIN":
            return None

        if code not in articles:
            print("❌ Code article inconnu.")
            continue

        if articles[code]["stock"] <= 0:
            print("❌ Cet article est actuellement en rupture de stock.")
            continue

        return code


# ============================================================
# AJOUT AU PANIER
# ============================================================

def ajouter_au_panier(articles, panier):

    code = choisir_article(articles)

    if code is None:
        return False

    article = articles[code]

    print(f"\nArticle sélectionné : {article['nom']}")
    print(f"Prix unitaire       : {article['prix']:,} FCFA")
    print(f"Stock disponible    : {article['stock']}")

    while True:

        try:
            quantite = int(
                input("Quantité souhaitée : ")
            )

            if quantite <= 0:
                print("❌ La quantité doit être supérieure à zéro.")
                continue

            # Vérifier la quantité déjà présente dans le panier
            quantite_deja_dans_panier = panier.get(code, 0)

            if quantite + quantite_deja_dans_panier > article["stock"]:
                print(
                    f"❌ Stock insuffisant. "
                    f"Stock disponible : {article['stock']}"
                )
                continue

            panier[code] = quantite_deja_dans_panier + quantite

            print(
                f"✅ {quantite} x {article['nom']} "
                f"ajouté(s) au panier."
            )

            return True

        except ValueError:
            print("❌ Veuillez entrer un nombre entier.")


# ============================================================
# AFFICHER LE PANIER
# ============================================================

def afficher_panier(articles, panier):

    if not panier:
        print("\n🛒 Le panier est vide.")
        return 0

    print("\n" + "=" * 75)
    print("                              PANIER")
    print("=" * 75)

    print(
        f"{'ARTICLE':<30}"
        f"{'QTÉ':>8}"
        f"{'PRIX UNIT.':>17}"
        f"{'TOTAL':>18}"
    )

    print("-" * 75)

    total_general = 0

    for code, quantite in panier.items():

        article = articles[code]

        prix_unitaire = article["prix"]
        total_article = prix_unitaire * quantite

        total_general += total_article

        print(
            f"{article['nom']:<30}"
            f"{quantite:>8}"
            f"{prix_unitaire:>15,} FCFA"
            f"{total_article:>15,} FCFA"
        )

    print("-" * 75)

    print(
        f"{'TOTAL À PAYER':<55}"
        f"{total_general:>15,} FCFA"
    )

    print("=" * 75)

    return total_general


# ============================================================
# SAISIE DES INFORMATIONS CLIENT
# ============================================================

def informations_client():

    print("\n" + "=" * 50)
    print("              INFORMATIONS CLIENT")
    print("=" * 50)

    while True:

        nom = input("Nom du client : ").strip()

        if nom:
            break

        print("❌ Le nom ne peut pas être vide.")

    telephone = input("Téléphone : ").strip()

    return {
        "nom": nom,
        "telephone": telephone
    }


# ============================================================
# GÉNÉRATION DE LA FACTURE
# ============================================================

def generer_facture(client, articles, panier, numero_facture):

    date = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    total_general = 0

    lignes = []

    for code, quantite in panier.items():

        article = articles[code]

        total_article = article["prix"] * quantite

        total_general += total_article

        lignes.append({
            "code": code,
            "article": article["nom"],
            "quantite": quantite,
            "prix_unitaire": article["prix"],
            "total": total_article
        })

    facture = {
        "numero": numero_facture,
        "date": date,
        "client": client,
        "articles": lignes,
        "total": total_general
    }

    return facture


# ============================================================
# AFFICHER LA FACTURE
# ============================================================

def afficher_facture(facture):

    print("\n")
    print("=" * 75)
    print("                         MA BOUTIQUE")
    print("                           FACTURE")
    print("=" * 75)

    print(f"Facture n° : {facture['numero']}")
    print(f"Date       : {facture['date']}")
    print(f"Client     : {facture['client']['nom']}")
    print(f"Téléphone  : {facture['client']['telephone']}")

    print("-" * 75)

    print(
        f"{'ARTICLE':<30}"
        f"{'QTÉ':>8}"
        f"{'PRIX':>17}"
        f"{'TOTAL':>18}"
    )

    print("-" * 75)

    for ligne in facture["articles"]:

        print(
            f"{ligne['article']:<30}"
            f"{ligne['quantite']:>8}"
            f"{ligne['prix_unitaire']:>15,} FCFA"
            f"{ligne['total']:>15,} FCFA"
        )

    print("-" * 75)

    print(
        f"{'TOTAL À PAYER':<55}"
        f"{facture['total']:>15,} FCFA"
    )

    print("=" * 75)
    print("                 Merci pour votre achat !")
    print("=" * 75)


# ============================================================
# ACTUALISATION DE LA BASE DE DONNÉES
# ============================================================

def actualiser_stock(articles, panier):

    for code, quantite in panier.items():

        articles[code]["stock"] -= quantite

    sauvegarder_articles(articles)

    print("\n✅ La base de données des articles a été actualisée.")


# ============================================================
# PASSER UNE COMMANDE
# ============================================================

def passer_commande(articles, commandes):

    panier = {}

    print("\n")
    print("=" * 75)
    print("                         NOUVELLE COMMANDE")
    print("=" * 75)

    # Ajouter des articles
    while True:

        afficher_articles(articles)

        ajoute = ajouter_au_panier(articles, panier)

        if not ajoute:
            break

        afficher_panier(articles, panier)

        continuer = input(
            "\nAjouter un autre article ? (o/n) : "
        ).lower().strip()

        if continuer != "o":
            break

    # Vérifier que le panier n'est pas vide
    if not panier:

        print("\n❌ Commande annulée : panier vide.")
        return

    # Afficher le panier final
    total = afficher_panier(articles, panier)

    # Informations du client
    client = informations_client()

    # Confirmation
    print("\n" + "=" * 50)
    print(f"TOTAL À PAYER : {total:,} FCFA")
    print("=" * 50)

    confirmation = input(
        "Confirmer la commande ? (o/n) : "
    ).lower().strip()

    if confirmation != "o":

        print("\n❌ Commande annulée.")
        return

    # Génération du numéro de facture
    numero_facture = f"FAC-{len(commandes) + 1:05d}"

    # Générer la facture
    facture = generer_facture(
        client,
        articles,
        panier,
        numero_facture
    )

    # Actualiser le stock
    actualiser_stock(articles, panier)

    # Enregistrer la commande
    commandes.append(facture)

    sauvegarder_commandes(commandes)

    # Afficher la facture
    afficher_facture(facture)

    print("\n✅ Commande enregistrée avec succès.")


# ============================================================
# HISTORIQUE DES COMMANDES
# ============================================================

def afficher_historique(commandes):

    if not commandes:

        print("\n📋 Aucune commande enregistrée.")
        return

    print("\n" + "=" * 80)
    print("                         HISTORIQUE DES COMMANDES")
    print("=" * 80)

    for commande in commandes:

        print(
            f"\nFacture : {commande['numero']}"
        )

        print(
            f"Client  : {commande['client']['nom']}"
        )

        print(
            f"Date    : {commande['date']}"
        )

        print(
            f"Total   : {commande['total']:,} FCFA"
        )

        print("-" * 50)


# ============================================================
# MENU PRINCIPAL
# ============================================================

def menu():

    articles = charger_articles()
    commandes = charger_commandes()

    while True:

        print("\n")
        print("=" * 60)
        print("              🛒 MA BOUTIQUE")
        print("=" * 60)

        print("1. Afficher les articles")
        print("2. Passer une commande")
        print("3. Afficher l'historique des commandes")
        print("4. Quitter")

        print("=" * 60)

        choix = input("Votre choix : ").strip()

        if choix == "1":

            afficher_articles(articles)

        elif choix == "2":

            passer_commande(
                articles,
                commandes
            )

        elif choix == "3":

            afficher_historique(
                commandes
            )

        elif choix == "4":

            print("\nMerci et à bientôt ! 👋")
            break

        else:

            print(
                "\n❌ Choix invalide. "
                "Veuillez sélectionner une option de 1 à 4."
            )


# ============================================================
# PROGRAMME PRINCIPAL
# ============================================================

if __name__ == "__main__":
    menu()
```

### Fichiers créés automatiquement

Lorsque tu lances le programme, il crée automatiquement :

```text
articles.json
commandes.json
```

`articles.json` constitue la **base de données du stock**. Par exemple :

```json
{
    "A001": {
        "nom": "Ordinateur portable",
        "prix": 350000,
        "stock": 10
    },
    "A002": {
        "nom": "Téléphone Samsung",
        "prix": 180000,
        "stock": 15
    }
}
```

Après une vente de 2 ordinateurs, le stock passe automatiquement de `10` à `8`.

`commandes.json` conserve quant à lui l'historique des factures.

### Fonctionnement

```text
                 ┌─────────────────┐
                 │     BOUTIQUE    │
                 └────────┬────────┘
                          │
              ┌───────────┴───────────┐
              │                       │
       Afficher les articles     Passer commande
                                      │
                                      ▼
                                Choisir articles
                                      │
                                      ▼
                                Vérifier stock
                                      │
                                      ▼
                                  Panier
                                      │
                                      ▼
                              Informations client
                                      │
                                      ▼
                                Confirmation
                                      │
                         ┌────────────┴────────────┐
                         │                         │
                         ▼                         ▼
                    Facture                  Mise à jour BD
                         │                         │
                         └────────────┬────────────┘
                                      ▼
                              Enregistrement
                              de la commande
```

**Important :** cette version utilise des fichiers JSON, ce qui est pratique pour commencer. Pour une vraie application de boutique, je te conseille ensuite de remplacer `articles.json` par **SQLite** (une vraie petite base de données), puis de connecter le programme à une interface **Streamlit**. Cela permettrait d'avoir une boutique avec des boutons, un panier, une page de facture et une gestion du stock directement dans le navigateur.
