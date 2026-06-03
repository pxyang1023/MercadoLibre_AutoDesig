# Next Steps

## 1. Build the `product_plan.json` generator

Create a script that reads `input/products/products_sample.csv` and generates a structured product plan for each pending product.

The plan should include copywriting, image themes, prompt text, and composition instructions for all 7 output images.

## 2. Build the image composition script

Create a Python script that reads product data, source images, generated assets, and templates, then exports final 1024 x 1024 PNG images.

The script should follow the naming list in `config/project_config.json`.

## 3. Build the ComfyUI API caller

Create a script that sends prompt workflows to the local ComfyUI API at `http://127.0.0.1:8188` and saves generated assets for each product.

## 4. Build a local HTTP service for n8n

Create a lightweight local service that n8n can call to trigger product processing.

The service should expose endpoints for starting a job, checking job status, and returning output paths.