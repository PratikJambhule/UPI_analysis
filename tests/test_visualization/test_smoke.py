"""Smoke tests — verify all modules import without errors."""


def test_app_importable():
    """The app module should import without errors."""
    import src.visualization.app  # noqa: F401


def test_all_pages_importable():
    """All page modules should import without errors."""
    from src.visualization.pages import (  # noqa: F401
        overview,
        executive_summary,
        growth_trends,
        market_share,
        app_dynamics,
        geographic_insights,
        district_deep_dive,
        cash_displacement,
        forecasting,
        users_devices,
        methodology,
    )


def test_all_components_importable():
    """All component modules should import without errors."""
    from src.visualization.components import (  # noqa: F401
        charts, kpi_cards, maps, filters, data_loader, styles,
    )


def test_page_modules_have_render():
    """Each page module should expose a render() function."""
    from src.visualization.pages import (
        overview,
        executive_summary,
        growth_trends,
        market_share,
        app_dynamics,
        geographic_insights,
        district_deep_dive,
        cash_displacement,
        forecasting,
        users_devices,
        methodology,
    )
    for module in [overview, executive_summary, growth_trends, market_share,
                   app_dynamics, geographic_insights, district_deep_dive,
                   cash_displacement, forecasting, users_devices, methodology]:
        assert callable(getattr(module, "render", None)), (
            f"{module.__name__} missing render() function"
        )
