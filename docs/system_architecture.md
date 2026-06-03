# System Architecture

This project implements a simplified AI ecommerce detail-image automation pipeline for MercadoLibre product image generation.

## 1. Product Input

Product data starts from structured CSV files under `input/products`. Each row describes one product, including product ID, name, category, language, target market, selling points, capacity, source image filename, and processing status.

Source product images are stored under `input/images`. The `input_image` field in the CSV should match a file in that folder.

## 2. AI Copywriting / Prompt Planning

The copywriting and prompt-planning layer converts product data into a structured product plan. This plan should include:

- Marketplace-ready Spanish copy for LatAm.
- Image-by-image messaging for 1 main image and 6 detail images.
- Prompt text for ComfyUI asset generation.
- Layout hints for Python template composition.

A future generator can output `product_plan.json` for each product.

## 3. ComfyUI Asset Generation

ComfyUI is responsible for generating or enhancing visual assets used by the final detail images. The project configuration points to the local ComfyUI API at `http://127.0.0.1:8188`.

This layer can generate backgrounds, lifestyle scenes, flavor visuals, ingredient elements, and supporting graphics. The generated assets should be saved in a predictable location for the composition script to consume.

## 4. Python Template Composition

Python scripts will combine product images, generated assets, copywriting, and layout templates into final ecommerce images.

The composition layer should:

- Use a 1024 x 1024 canvas.
- Produce 7 images per product.
- Follow the output names defined in `config/project_config.json`.
- Save final PNG files under `output`.

## 5. n8n Orchestration

n8n will later orchestrate the full automation workflow. It can trigger local scripts or a local HTTP service to process products, call AI planning, request ComfyUI generation, run image composition, and update downstream systems.

Workflow definitions and exported n8n flows can be stored under `workflows`.

## 6. Export / Upload / Sheet Backfill

After image generation, the export layer should prepare files for marketplace upload and record processing results.

Planned responsibilities include:

- Export final PNG images.
- Upload generated assets to storage or marketplace tooling.
- Backfill status, output paths, and errors into a spreadsheet or database.
- Mark completed products so the same item is not processed repeatedly.