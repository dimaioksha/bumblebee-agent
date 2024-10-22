from src.bootstrap import Bootstrap, get_prod_bootstrap

if __name__ == "__main__":
    bootstrap: Bootstrap = get_prod_bootstrap()
    # somehow run app using bootstrap as state
