from jinja2 import Environment, FileSystemLoader
import os


def render_full_unit_to_html(all_plans_dict_list, unit_title, image_cache,
                             output_filename="outputs/Full_Unit_Lesson_Plan.html"):
    env = Environment(loader=FileSystemLoader('templates'))
    template = env.get_template('lesson_plan_template.html')

    html_out = template.render(all_plans=all_plans_dict_list, unit_title=unit_title)

    for seq_id, base64_str in image_cache.items():
        tag = f"[IMAGE_TAG_{seq_id}]"
        img_html = f'<br><img src="data:image/jpeg;base64,{base64_str}" style="max-width: 600px; border: 1px solid #ccc; border-radius: 5px;" alt="Textbook Image"><br>'
        html_out = html_out.replace(tag, img_html)

    os.makedirs(os.path.dirname(output_filename), exist_ok=True)

    with open(output_filename, "w", encoding="utf-8") as f:
        f.write(html_out)

    print(f"\n🎉 THÀNH CÔNG! Đã gộp giáo án và nhúng thành công {len(image_cache)} ảnh vào file: {output_filename}")