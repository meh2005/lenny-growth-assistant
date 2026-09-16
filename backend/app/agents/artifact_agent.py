import re


def build_artifact_html(
    title: str,
    content: str,
) -> str:
    """
    Build a safe standalone HTML artifact.

    The artifact is intentionally self-contained so it can be
    rendered inside the frontend sandboxed iframe.
    """

    # Remove potentially dangerous script blocks.
    safe_content = re.sub(
        r"<script\b[^>]*>.*?</script>",
        "",
        content,
        flags=re.IGNORECASE | re.DOTALL,
    )

    # Remove inline event handlers such as onclick/onload.
    safe_content = re.sub(
        r"\son[a-z]+\s*=\s*(['\"]).*?\1",
        "",
        safe_content,
        flags=re.IGNORECASE | re.DOTALL,
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">

  <title>{title}</title>

  <style>
    * {{
      box-sizing: border-box;
    }}

    body {{
      margin: 0;
      padding: 40px;
      font-family:
        Inter,
        system-ui,
        -apple-system,
        BlinkMacSystemFont,
        "Segoe UI",
        sans-serif;
      background: #f8f7f4;
      color: #222;
      line-height: 1.6;
    }}

    .artifact {{
      max-width: 820px;
      margin: 0 auto;
      padding: 36px;
      background: #ffffff;
      border: 1px solid #e5e2dc;
      border-radius: 16px;
      box-shadow: 0 8px 30px rgba(0, 0, 0, 0.06);
    }}

    h1 {{
      margin-top: 0;
      font-size: 30px;
      line-height: 1.2;
    }}

    h2 {{
      margin-top: 28px;
      font-size: 20px;
    }}

    p {{
      color: #555;
    }}

    ul {{
      padding-left: 22px;
    }}

    li {{
      margin: 8px 0;
    }}

    .takeaway {{
      margin-top: 28px;
      padding: 18px;
      border-radius: 10px;
      background: #f4f2ed;
    }}

    .takeaway strong {{
      display: block;
      margin-bottom: 5px;
    }}
  </style>
</head>

<body>
  <article class="artifact">
    <h1>{title}</h1>

    {safe_content}
  </article>
</body>
</html>
"""