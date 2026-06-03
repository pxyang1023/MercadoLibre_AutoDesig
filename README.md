# MercadoLibre AutoDesign

## Project Goal

This project is a simplified AI ecommerce detail-image automation workflow for MercadoLibre product image generation.

The target workflow is:

Product information + product image -> AI copywriting and prompt planning -> ComfyUI asset generation -> Python template composition -> output 1 main image + 6 detail images -> future n8n integration.

## Planned Output

The system will generate 7 ecommerce images per product:

1. Main image on white background
2. Selling points image
3. Flavor image
4. Ingredients image
5. Lifestyle image
6. Capacity image
7. Summary image

## Project Structure

- `input/images`: Source product images.
- `input/products`: Product CSV input files.
- `output`: Generated image output.
- `templates`: Composition templates and layout assets.
- `scripts`: Python automation scripts.
- `workflows`: ComfyUI and n8n workflow files.
- `config`: Project configuration.
- `docs`: Architecture notes and implementation roadmap.