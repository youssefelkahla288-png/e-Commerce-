            "\n🔎 TEST DE RECHERCHE"
        )

        print(
            "Hoodies noirs taille M "
            "à moins de 150 DT :\n"
        )

        results = search_products(
            connection,
            category="Hoodies",
            color="Noir",
            size="M",
            max_price=150,
            limit=5,
        )

        if not results:
            print(
                "Aucun article trouvé."
            )

        else:

            for product in results:

                (
                    product_id,
                    name,
                    description,
                    category,
                    brand,
                    size,
                    color,
                    condition,
                    style,
                    season,
                    price,
                    rating,
                    num_reviews,
                    seller,
                ) = product

                print(
                    f"#{product_id} | "
                    f"{name} | "
                    f"{price:.2f} DT | "
                    f"{rating}/5 | "
                    f"{condition}"
                )

    finally:

        connection.close()
        
# =========================================================
# ENTRY POINT
# =========================================================

if __name__ == "__main__":
    main()