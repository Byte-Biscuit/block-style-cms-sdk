from block_style_cms_sdk.markdown.images import (
    collect_relative_image_srcs,
    is_relative_image_src,
    is_skippable_image_src,
    rewrite_all_image_srcs,
    rewrite_image_src,
)


def test_skippable_and_relative() -> None:
    assert is_skippable_image_src("/images/a.webp")
    assert is_skippable_image_src("https://cdn.example/a.png")
    assert is_relative_image_src("./assets/x.png")
    assert is_relative_image_src("assets/x.png")
    assert not is_relative_image_src("/images/x.webp")


def test_collect_relative() -> None:
    md = """
![a](./assets/a.png)
![b](/images/b.webp)
![c](https://cdn.example/c.png)
<img src="assets/d.jpg" />
"""
    assert collect_relative_image_srcs(md) == ["./assets/a.png", "assets/d.jpg"]


def test_rewrite() -> None:
    md = "before ![alt](./assets/a.png) after"
    assert (
        rewrite_image_src(md, "./assets/a.png", "/images/a.webp")
        == "before ![alt](/images/a.webp) after"
    )


def test_rewrite_all() -> None:
    md = "![a](./assets/a.png) and ![b](assets/b.png)"
    out = rewrite_all_image_srcs(
        md,
        {
            "./assets/a.png": "/images/a.webp",
            "assets/b.png": "/images/b.webp",
        },
    )
    assert "/images/a.webp" in out
    assert "/images/b.webp" in out
    assert "./assets/" not in out
