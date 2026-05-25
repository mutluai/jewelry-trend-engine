You are a jewelry product analyst. Extract structured attributes from the jewelry product below.

Title: {title}
Description: {description}

Return ONLY a valid JSON object with these exact fields:
```json
{
  "material": "primary material (e.g. gold-plated, sterling silver, rose gold, brass)",
  "stone": "primary stone/gem or null if none (e.g. diamond, pearl, emerald, opal)",
  "style": "primary style (e.g. minimalist, vintage, boho, classic, statement, dainty, geometric)",
  "category": "jewelry category (rings, necklaces, bracelets, earrings, anklets)",
  "color": "primary color description (e.g. gold, silver, rose gold, multicolor)",
  "target_gender": "women | men | unisex",
  "price_tier": "budget | mid | premium | luxury (budget<30, mid<80, premium<150, luxury>=150 USD)",
  "theme": "design theme or null (e.g. nature, celestial, love, spiritual, art deco, floral, ocean)",
  "style_tags": ["array", "of", "up to 5 descriptive tags"],
  "confidence": 0.9
}
```

Rules:
- Use lowercase for all values
- Return null for fields you cannot determine
- style_tags should capture key features not covered by other fields
- confidence is your certainty 0.0-1.0
