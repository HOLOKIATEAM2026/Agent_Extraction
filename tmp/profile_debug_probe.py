from agent.supabase_store import SupabaseStore
from api.main import get_profile_evolution, get_profile_summary


def main() -> None:
    store = SupabaseStore()
    profiles = store._get(
        "entreprise_profil",
        params={
            "nom": "eq.ATLASPAY_MAROC_SA",
            "select": "id,user_id,nom,score_nist_moyen,score_data_moyen,nb_rapports_analyses",
            "limit": "1",
        },
    )
    print("PROFILES", profiles)
    if not profiles:
        return

    user_id = profiles[0].get("user_id")
    auth = {"user": {"id": user_id}, "token": store.token}
    print("EVOLUTION", get_profile_evolution(company="ATLASPAY_MAROC_SA", limit=30, user_auth=auth))
    print("SUMMARY", get_profile_summary(company="ATLASPAY_MAROC_SA", user_auth=auth))


if __name__ == "__main__":
    main()
