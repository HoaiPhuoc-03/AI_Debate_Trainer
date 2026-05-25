from __future__ import annotations

import unicodedata
from collections import Counter
from datetime import datetime, timezone


TOPIC_CREATED_AT = datetime(2026, 5, 25, tzinfo=timezone.utc).isoformat()

TOPIC_CATEGORIES = [
    {
        "id": "education",
        "name": "Giáo dục",
        "description": "Các chủ đề liên quan đến trường học, học tập, phương pháp giáo dục.",
    },
    {
        "id": "technology",
        "name": "Công nghệ",
        "description": "Các chủ đề về AI, dữ liệu, mạng xã hội và công nghệ trong đời sống.",
    },
    {
        "id": "society",
        "name": "Xã hội",
        "description": "Các vấn đề đời sống, cộng đồng, hành vi xã hội và quan hệ giữa người với người.",
    },
    {
        "id": "economy",
        "name": "Kinh tế",
        "description": "Các chủ đề về tiền bạc, tiêu dùng, lao động, thuế và khởi nghiệp.",
    },
    {
        "id": "ethics",
        "name": "Đạo đức",
        "description": "Các tranh luận về đúng sai, trách nhiệm, công bằng và ranh giới đạo đức.",
    },
    {
        "id": "policy",
        "name": "Chính trị",
        "description": "Các chủ đề chính sách công, quyền công dân, quản trị và dịch vụ công.",
    },
    {
        "id": "environment",
        "name": "Môi trường",
        "description": "Các vấn đề về khí hậu, rác thải, năng lượng và phát triển bền vững.",
    },
    {
        "id": "health",
        "name": "Sức khỏe",
        "description": "Các chủ đề về thể chất, tinh thần, dinh dưỡng và sức khỏe học đường.",
    },
    {
        "id": "culture",
        "name": "Văn hóa",
        "description": "Các chủ đề về lối sống, thần tượng, phim ảnh và bản sắc văn hóa.",
    },
    {
        "id": "media",
        "name": "Truyền thông",
        "description": "Các tranh luận về influencer, quảng cáo, tin giả và nền tảng nội dung.",
    },
]


SEED_TOPICS = [
    {
        "id": "edu_ai_homework",
        "title": "Học sinh có nên được dùng AI để làm bài tập?",
        "category": "Giáo dục",
        "difficulty": "Trung cấp",
        "tags": ["AI", "học tập", "đạo đức học thuật"],
        "description": "Chủ đề xoay quanh việc sử dụng AI trong học tập và ranh giới giữa hỗ trợ và gian lận.",
        "suggested_stance": ["Ủng hộ", "Phản đối"],
    },
    {
        "id": "edu_phone_ban",
        "title": "Trường học có nên cấm điện thoại trong giờ học?",
        "category": "Giáo dục",
        "difficulty": "Cơ bản",
        "tags": ["điện thoại", "tập trung", "kỷ luật"],
        "description": "Tranh luận về sự tập trung, quyền tự quản và vai trò của thiết bị số trong lớp học.",
        "suggested_stance": ["Ủng hộ", "Phản đối"],
    },
    {
        "id": "edu_no_homework",
        "title": "Có nên bỏ bài tập về nhà?",
        "category": "Giáo dục",
        "difficulty": "Cơ bản",
        "tags": ["bài tập", "áp lực", "gia đình"],
        "description": "Chủ đề gần gũi về cân bằng giữa luyện tập, nghỉ ngơi và thời gian cá nhân.",
        "suggested_stance": ["Ủng hộ", "Phản đối"],
    },
    {
        "id": "edu_grades_measure",
        "title": "Điểm số có còn là thước đo tốt cho năng lực học sinh?",
        "category": "Giáo dục",
        "difficulty": "Trung cấp",
        "tags": ["điểm số", "đánh giá", "năng lực"],
        "description": "Đặt câu hỏi về cách đo năng lực, động lực học tập và áp lực thành tích.",
        "suggested_stance": ["Ủng hộ", "Phản đối"],
    },
    {
        "id": "edu_critical_thinking_university",
        "title": "Đại học có nên bắt buộc học kỹ năng phản biện?",
        "category": "Giáo dục",
        "difficulty": "Trung cấp",
        "tags": ["đại học", "phản biện", "kỹ năng"],
        "description": "Thảo luận về vai trò của tư duy phản biện trong học tập, nghề nghiệp và công dân số.",
        "suggested_stance": ["Ủng hộ", "Phản đối"],
    },
    {
        "id": "tech_ai_teacher",
        "title": "AI có nên thay thế một phần giáo viên?",
        "category": "Công nghệ",
        "difficulty": "Nâng cao",
        "tags": ["AI", "giáo viên", "cá nhân hóa"],
        "description": "Tranh luận về hiệu quả cá nhân hóa, vai trò con người và rủi ro phụ thuộc công nghệ.",
        "suggested_stance": ["Ủng hộ", "Phản đối"],
    },
    {
        "id": "tech_social_focus",
        "title": "Mạng xã hội có làm giảm khả năng tập trung?",
        "category": "Công nghệ",
        "difficulty": "Cơ bản",
        "tags": ["mạng xã hội", "tập trung", "thói quen"],
        "description": "Một chủ đề đời sống về thói quen số, sự chú ý và cách dùng mạng xã hội có kiểm soát.",
        "suggested_stance": ["Ủng hộ", "Phản đối"],
    },
    {
        "id": "tech_tiktok_time_limit",
        "title": "Có nên giới hạn thời gian sử dụng TikTok ở thanh thiếu niên?",
        "category": "Công nghệ",
        "difficulty": "Trung cấp",
        "tags": ["TikTok", "thanh thiếu niên", "nền tảng số"],
        "description": "Cân nhắc giữa tự do cá nhân, sức khỏe tinh thần và trách nhiệm của nền tảng.",
        "suggested_stance": ["Ủng hộ", "Phản đối"],
    },
    {
        "id": "tech_personal_data_property",
        "title": "Dữ liệu cá nhân có nên được xem là tài sản riêng?",
        "category": "Công nghệ",
        "difficulty": "Nâng cao",
        "tags": ["dữ liệu", "quyền riêng tư", "tài sản số"],
        "description": "Chủ đề về quyền sở hữu dữ liệu, mô hình kinh doanh số và bảo vệ người dùng.",
        "suggested_stance": ["Ủng hộ", "Phản đối"],
    },
    {
        "id": "tech_robot_eldercare",
        "title": "Robot có nên được dùng để chăm sóc người cao tuổi?",
        "category": "Công nghệ",
        "difficulty": "Trung cấp",
        "tags": ["robot", "chăm sóc", "người cao tuổi"],
        "description": "Tranh luận về tiện ích, cảm xúc con người, chi phí và đạo đức chăm sóc.",
        "suggested_stance": ["Ủng hộ", "Phản đối"],
    },
    {
        "id": "soc_cyberbullying_penalty",
        "title": "Có nên phạt nặng hành vi bắt nạt trên mạng?",
        "category": "Xã hội",
        "difficulty": "Trung cấp",
        "tags": ["bắt nạt mạng", "an toàn", "trách nhiệm"],
        "description": "Bàn về tác hại tinh thần, giáo dục hành vi và mức độ can thiệp của luật lệ.",
        "suggested_stance": ["Ủng hộ", "Phản đối"],
    },
    {
        "id": "soc_young_independent",
        "title": "Người trẻ có nên sống tự lập sớm?",
        "category": "Xã hội",
        "difficulty": "Cơ bản",
        "tags": ["người trẻ", "tự lập", "gia đình"],
        "description": "Một chủ đề gần gũi về trưởng thành, tài chính, trách nhiệm và sự hỗ trợ từ gia đình.",
        "suggested_stance": ["Ủng hộ", "Phản đối"],
    },
    {
        "id": "soc_remote_work",
        "title": "Làm việc từ xa có tốt hơn làm việc tại văn phòng?",
        "category": "Xã hội",
        "difficulty": "Trung cấp",
        "tags": ["làm việc từ xa", "văn phòng", "năng suất"],
        "description": "So sánh năng suất, giao tiếp đội nhóm, cân bằng đời sống và văn hóa công ty.",
        "suggested_stance": ["Ủng hộ", "Phản đối"],
    },
    {
        "id": "soc_public_transport",
        "title": "Có nên khuyến khích giao thông công cộng hơn xe cá nhân?",
        "category": "Xã hội",
        "difficulty": "Trung cấp",
        "tags": ["giao thông", "đô thị", "cộng đồng"],
        "description": "Chủ đề về ùn tắc, môi trường, tiện lợi cá nhân và đầu tư hạ tầng đô thị.",
        "suggested_stance": ["Ủng hộ", "Phản đối"],
    },
    {
        "id": "soc_celeb_role_model",
        "title": "Người nổi tiếng có trách nhiệm làm gương không?",
        "category": "Xã hội",
        "difficulty": "Cơ bản",
        "tags": ["người nổi tiếng", "trách nhiệm", "ảnh hưởng"],
        "description": "Tranh luận về ảnh hưởng xã hội, quyền riêng tư và trách nhiệm với người hâm mộ.",
        "suggested_stance": ["Ủng hộ", "Phản đối"],
    },
    {
        "id": "eco_personal_finance_school",
        "title": "Có nên dạy quản lý tài chính cá nhân từ cấp 3?",
        "category": "Kinh tế",
        "difficulty": "Cơ bản",
        "tags": ["tài chính cá nhân", "cấp 3", "kỹ năng sống"],
        "description": "Đề cập đến năng lực quản lý tiền, tiêu dùng thông minh và chuẩn bị cho đời sống độc lập.",
        "suggested_stance": ["Ủng hộ", "Phản đối"],
    },
    {
        "id": "eco_online_spending",
        "title": "Mua sắm online có làm người trẻ chi tiêu mất kiểm soát?",
        "category": "Kinh tế",
        "difficulty": "Cơ bản",
        "tags": ["mua sắm online", "chi tiêu", "người trẻ"],
        "description": "Chủ đề đời sống về khuyến mãi, ví điện tử, thói quen mua sắm và tự kiểm soát.",
        "suggested_stance": ["Ủng hộ", "Phản đối"],
    },
    {
        "id": "eco_green_tax",
        "title": "Có nên đánh thuế cao hơn với sản phẩm gây hại môi trường?",
        "category": "Kinh tế",
        "difficulty": "Nâng cao",
        "tags": ["thuế", "môi trường", "tiêu dùng"],
        "description": "Cân nhắc giữa thay đổi hành vi tiêu dùng, công bằng xã hội và tác động lên doanh nghiệp.",
        "suggested_stance": ["Ủng hộ", "Phản đối"],
    },
    {
        "id": "eco_startup_university",
        "title": "Startup có nên được ưu tiên hỗ trợ trong trường đại học?",
        "category": "Kinh tế",
        "difficulty": "Trung cấp",
        "tags": ["startup", "đại học", "đổi mới"],
        "description": "Tranh luận về khởi nghiệp, nghiên cứu ứng dụng, rủi ro thương mại hóa giáo dục.",
        "suggested_stance": ["Ủng hộ", "Phản đối"],
    },
    {
        "id": "eco_minimum_wage_yearly",
        "title": "Lương tối thiểu có nên tăng hằng năm?",
        "category": "Kinh tế",
        "difficulty": "Nâng cao",
        "tags": ["lương tối thiểu", "lao động", "lạm phát"],
        "description": "Đặt vấn đề giữa bảo vệ người lao động, chi phí doanh nghiệp và sức mua xã hội.",
        "suggested_stance": ["Ủng hộ", "Phản đối"],
    },
    {
        "id": "eth_ai_writing_cheating",
        "title": "Dùng AI viết bài có phải là gian lận không?",
        "category": "Đạo đức",
        "difficulty": "Trung cấp",
        "tags": ["AI", "gian lận", "học thuật"],
        "description": "Phân tích ranh giới giữa công cụ hỗ trợ, sáng tạo cá nhân và trung thực học thuật.",
        "suggested_stance": ["Ủng hộ", "Phản đối"],
    },
    {
        "id": "eth_ai_camera_school",
        "title": "Có nên sử dụng camera AI để giám sát học sinh?",
        "category": "Đạo đức",
        "difficulty": "Nâng cao",
        "tags": ["camera AI", "giám sát", "quyền riêng tư"],
        "description": "Chủ đề về an toàn trường học, quyền riêng tư, minh bạch dữ liệu và sự tin tưởng.",
        "suggested_stance": ["Ủng hộ", "Phản đối"],
    },
    {
        "id": "eth_public_grades",
        "title": "Có nên công khai điểm số của học sinh trong lớp?",
        "category": "Đạo đức",
        "difficulty": "Cơ bản",
        "tags": ["điểm số", "riêng tư", "động lực"],
        "description": "Bàn về động lực cạnh tranh, xấu hổ, công bằng và quyền riêng tư của học sinh.",
        "suggested_stance": ["Ủng hộ", "Phản đối"],
    },
    {
        "id": "eth_ai_hiring",
        "title": "AI có nên được quyền đưa ra quyết định tuyển dụng?",
        "category": "Đạo đức",
        "difficulty": "Nâng cao",
        "tags": ["AI", "tuyển dụng", "thiên kiến"],
        "description": "Tranh luận về hiệu quả, minh bạch, thiên kiến thuật toán và trách nhiệm con người.",
        "suggested_stance": ["Ủng hộ", "Phản đối"],
    },
    {
        "id": "eth_cancel_scandal",
        "title": "Có nên tha thứ cho người nổi tiếng sau scandal?",
        "category": "Đạo đức",
        "difficulty": "Trung cấp",
        "tags": ["scandal", "tha thứ", "trách nhiệm xã hội"],
        "description": "Cân nhắc giữa sửa sai, hậu quả hành vi, văn hóa tẩy chay và quyền được thay đổi.",
        "suggested_stance": ["Ủng hộ", "Phản đối"],
    },
    {
        "id": "pol_student_policy_voice",
        "title": "Có nên cho học sinh tham gia góp ý chính sách giáo dục?",
        "category": "Chính trị",
        "difficulty": "Trung cấp",
        "tags": ["chính sách giáo dục", "học sinh", "tham gia"],
        "description": "Đề cập đến tiếng nói người học, năng lực góp ý và cách thiết kế chính sách gần thực tế hơn.",
        "suggested_stance": ["Ủng hộ", "Phản đối"],
    },
    {
        "id": "pol_digital_media_literacy",
        "title": "Có nên bắt buộc công dân học kỹ năng truyền thông số?",
        "category": "Chính trị",
        "difficulty": "Trung cấp",
        "tags": ["công dân số", "truyền thông số", "tin giả"],
        "description": "Chủ đề về năng lực đọc hiểu thông tin, an toàn số và trách nhiệm công dân.",
        "suggested_stance": ["Ủng hộ", "Phản đối"],
    },
    {
        "id": "pol_fake_news_control",
        "title": "Có nên siết chặt quản lý tin giả trên mạng xã hội?",
        "category": "Chính trị",
        "difficulty": "Nâng cao",
        "tags": ["tin giả", "mạng xã hội", "quản lý"],
        "description": "Cân bằng giữa chống thông tin sai lệch, tự do biểu đạt và nguy cơ kiểm duyệt quá mức.",
        "suggested_stance": ["Ủng hộ", "Phản đối"],
    },
    {
        "id": "pol_ai_public_service",
        "title": "Chính phủ có nên dùng AI trong dịch vụ công?",
        "category": "Chính trị",
        "difficulty": "Nâng cao",
        "tags": ["AI governance", "dịch vụ công", "minh bạch"],
        "description": "Tranh luận về hiệu quả hành chính, quyền riêng tư, trách nhiệm giải trình và niềm tin công chúng.",
        "suggested_stance": ["Ủng hộ", "Phản đối"],
    },
    {
        "id": "pol_digital_citizenship_school",
        "title": "Có nên mở rộng giáo dục công dân số trong nhà trường?",
        "category": "Chính trị",
        "difficulty": "Cơ bản",
        "tags": ["công dân số", "nhà trường", "an toàn mạng"],
        "description": "Bàn về cách học sinh ứng xử, bảo vệ dữ liệu và tham gia môi trường số có trách nhiệm.",
        "suggested_stance": ["Ủng hộ", "Phản đối"],
    },
    {
        "id": "env_plastic_bag_ban",
        "title": "Có nên cấm túi nilon dùng một lần?",
        "category": "Môi trường",
        "difficulty": "Cơ bản",
        "tags": ["túi nilon", "rác thải", "tiêu dùng"],
        "description": "Chủ đề gần gũi về thói quen mua sắm, chi phí thay thế và tác động môi trường.",
        "suggested_stance": ["Ủng hộ", "Phản đối"],
    },
    {
        "id": "env_school_recycling",
        "title": "Trường học có nên bắt buộc phân loại rác?",
        "category": "Môi trường",
        "difficulty": "Cơ bản",
        "tags": ["phân loại rác", "trường học", "thói quen xanh"],
        "description": "Tranh luận về giáo dục hành vi, tính khả thi và chi phí vận hành trong trường học.",
        "suggested_stance": ["Ủng hộ", "Phản đối"],
    },
    {
        "id": "env_gas_car_limit",
        "title": "Có nên hạn chế xe xăng trong thành phố lớn?",
        "category": "Môi trường",
        "difficulty": "Nâng cao",
        "tags": ["xe xăng", "đô thị", "khí thải"],
        "description": "Cân nhắc giữa ô nhiễm, hạ tầng giao thông, quyền đi lại và chuyển đổi phương tiện.",
        "suggested_stance": ["Ủng hộ", "Phản đối"],
    },
    {
        "id": "env_consumer_climate",
        "title": "Người tiêu dùng có trách nhiệm với biến đổi khí hậu không?",
        "category": "Môi trường",
        "difficulty": "Trung cấp",
        "tags": ["biến đổi khí hậu", "người tiêu dùng", "trách nhiệm"],
        "description": "Đặt câu hỏi về trách nhiệm cá nhân, doanh nghiệp và chính sách trong khủng hoảng khí hậu.",
        "suggested_stance": ["Ủng hộ", "Phản đối"],
    },
    {
        "id": "env_energy_price_saving",
        "title": "Có nên tăng giá điện để khuyến khích tiết kiệm năng lượng?",
        "category": "Môi trường",
        "difficulty": "Nâng cao",
        "tags": ["giá điện", "năng lượng", "công bằng"],
        "description": "Tranh luận về động lực tiết kiệm, tác động đến hộ thu nhập thấp và chính sách hỗ trợ.",
        "suggested_stance": ["Ủng hộ", "Phản đối"],
    },
    {
        "id": "health_sugary_drinks_school",
        "title": "Có nên giới hạn đồ uống có đường trong trường học?",
        "category": "Sức khỏe",
        "difficulty": "Cơ bản",
        "tags": ["đồ uống có đường", "trường học", "dinh dưỡng"],
        "description": "Chủ đề về sức khỏe học sinh, lựa chọn cá nhân và trách nhiệm của nhà trường.",
        "suggested_stance": ["Ủng hộ", "Phản đối"],
    },
    {
        "id": "health_mental_health_subject",
        "title": "Học sinh có nên được học sức khỏe tinh thần như môn chính khóa?",
        "category": "Sức khỏe",
        "difficulty": "Trung cấp",
        "tags": ["sức khỏe tinh thần", "học sinh", "chính khóa"],
        "description": "Bàn về nhận thức cảm xúc, áp lực học đường và cách đưa sức khỏe tinh thần vào giáo dục.",
        "suggested_stance": ["Ủng hộ", "Phản đối"],
    },
    {
        "id": "health_fast_food_ads",
        "title": "Có nên cấm quảng cáo đồ ăn nhanh cho trẻ em?",
        "category": "Sức khỏe",
        "difficulty": "Trung cấp",
        "tags": ["đồ ăn nhanh", "quảng cáo", "trẻ em"],
        "description": "Tranh luận về quyền quảng cáo, sức khỏe cộng đồng và khả năng tự lựa chọn của gia đình.",
        "suggested_stance": ["Ủng hộ", "Phản đối"],
    },
    {
        "id": "health_sleep_vs_extra_classes",
        "title": "Ngủ đủ có quan trọng hơn học thêm không?",
        "category": "Sức khỏe",
        "difficulty": "Cơ bản",
        "tags": ["giấc ngủ", "học thêm", "học sinh"],
        "description": "Một chủ đề thân thuộc về hiệu quả học tập, sức khỏe và áp lực thành tích.",
        "suggested_stance": ["Ủng hộ", "Phản đối"],
    },
    {
        "id": "health_school_psych_check",
        "title": "Có nên kiểm tra sức khỏe tâm lý định kỳ ở trường?",
        "category": "Sức khỏe",
        "difficulty": "Nâng cao",
        "tags": ["tâm lý học đường", "quyền riêng tư", "phòng ngừa"],
        "description": "Cân nhắc giữa phát hiện sớm, kỳ thị, bảo mật dữ liệu và năng lực hỗ trợ của nhà trường.",
        "suggested_stance": ["Ủng hộ", "Phản đối"],
    },
    {
        "id": "culture_online_negative_reviews",
        "title": "Review tiêu cực trên mạng có nên bị kiểm soát?",
        "category": "Văn hóa",
        "difficulty": "Trung cấp",
        "tags": ["review", "văn hóa mạng", "trách nhiệm"],
        "description": "Tranh luận về tự do đánh giá, danh dự cá nhân, doanh nghiệp và hành vi đám đông.",
        "suggested_stance": ["Ủng hộ", "Phản đối"],
    },
    {
        "id": "culture_movies_youth_behavior",
        "title": "Phim ảnh có ảnh hưởng mạnh đến hành vi giới trẻ không?",
        "category": "Văn hóa",
        "difficulty": "Cơ bản",
        "tags": ["phim ảnh", "giới trẻ", "hành vi"],
        "description": "Chủ đề về tác động văn hóa đại chúng, trách nhiệm gia đình và năng lực tự nhận thức.",
        "suggested_stance": ["Ủng hộ", "Phản đối"],
    },
    {
        "id": "culture_fandom_pressure",
        "title": "Văn hóa thần tượng có gây áp lực cho học sinh không?",
        "category": "Văn hóa",
        "difficulty": "Cơ bản",
        "tags": ["thần tượng", "học sinh", "áp lực"],
        "description": "Bàn về cảm hứng, chi tiêu, so sánh bản thân và ảnh hưởng của cộng đồng người hâm mộ.",
        "suggested_stance": ["Ủng hộ", "Phản đối"],
    },
    {
        "id": "culture_traditional_values_school",
        "title": "Trường học có nên dạy nhiều hơn về giá trị văn hóa truyền thống?",
        "category": "Văn hóa",
        "difficulty": "Trung cấp",
        "tags": ["truyền thống", "giáo dục", "bản sắc"],
        "description": "Cân bằng giữa bản sắc văn hóa, chương trình học hiện đại và sự đa dạng của học sinh.",
        "suggested_stance": ["Ủng hộ", "Phản đối"],
    },
    {
        "id": "culture_global_content",
        "title": "Nội dung giải trí quốc tế có làm giới trẻ xa rời văn hóa địa phương?",
        "category": "Văn hóa",
        "difficulty": "Nâng cao",
        "tags": ["toàn cầu hóa", "giải trí", "văn hóa địa phương"],
        "description": "Tranh luận về giao lưu văn hóa, bản sắc, thị hiếu và vai trò của nội dung trong nước.",
        "suggested_stance": ["Ủng hộ", "Phản đối"],
    },
    {
        "id": "media_influencer_ads",
        "title": "Influencer có trách nhiệm với nội dung họ quảng cáo không?",
        "category": "Truyền thông",
        "difficulty": "Trung cấp",
        "tags": ["influencer", "quảng cáo", "trách nhiệm"],
        "description": "Bàn về niềm tin công chúng, kiểm chứng sản phẩm và trách nhiệm khi có ảnh hưởng lớn.",
        "suggested_stance": ["Ủng hộ", "Phản đối"],
    },
    {
        "id": "media_short_video_harm",
        "title": "Có nên giới hạn nội dung độc hại trên nền tảng video ngắn?",
        "category": "Truyền thông",
        "difficulty": "Trung cấp",
        "tags": ["video ngắn", "nội dung độc hại", "kiểm duyệt"],
        "description": "Tranh luận về bảo vệ người dùng, tự do sáng tạo và trách nhiệm của nền tảng.",
        "suggested_stance": ["Ủng hộ", "Phản đối"],
    },
    {
        "id": "media_fake_news_label",
        "title": "Nền tảng mạng xã hội có nên gắn nhãn cảnh báo tin giả?",
        "category": "Truyền thông",
        "difficulty": "Nâng cao",
        "tags": ["tin giả", "mạng xã hội", "kiểm chứng"],
        "description": "Cân nhắc giữa minh bạch thông tin, sai sót kiểm chứng và quyền tiếp cận thông tin.",
        "suggested_stance": ["Ủng hộ", "Phản đối"],
    },
    {
        "id": "media_children_fast_news",
        "title": "Học sinh có nên được dạy cách kiểm chứng thông tin trên mạng?",
        "category": "Truyền thông",
        "difficulty": "Cơ bản",
        "tags": ["kiểm chứng", "học sinh", "truyền thông số"],
        "description": "Một chủ đề thực tế về đọc tin, nguồn đáng tin cậy và kỹ năng phản biện thông tin.",
        "suggested_stance": ["Ủng hộ", "Phản đối"],
    },
    {
        "id": "media_comments_real_name",
        "title": "Bình luận trên mạng có nên bắt buộc dùng tên thật?",
        "category": "Truyền thông",
        "difficulty": "Nâng cao",
        "tags": ["ẩn danh", "bình luận", "quyền riêng tư"],
        "description": "Đặt vấn đề giữa trách nhiệm phát ngôn, an toàn cá nhân và quyền ẩn danh chính đáng.",
        "suggested_stance": ["Ủng hộ", "Phản đối"],
    },
]


def _with_defaults(topic: dict) -> dict:
    return {
        **topic,
        "is_active": topic.get("is_active", True),
        "created_at": topic.get("created_at", TOPIC_CREATED_AT),
    }


TOPICS = [_with_defaults(topic) for topic in SEED_TOPICS]


def _key(value: str | None) -> str:
    text = str(value or "").casefold().replace("đ", "d")
    text = unicodedata.normalize("NFKD", text)
    text = "".join(character for character in text if not unicodedata.combining(character))
    return " ".join(text.split())


def _difficulty_key(value: str | None) -> str:
    key = _key(value)
    aliases = {
        "basic": "co ban",
        "easy": "co ban",
        "beginner": "co ban",
        "co ban": "co ban",
        "intermediate": "trung cap",
        "medium": "trung cap",
        "trung binh": "trung cap",
        "trung cap": "trung cap",
        "advanced": "nang cao",
        "hard": "nang cao",
        "expert": "nang cao",
        "nang cao": "nang cao",
    }
    return aliases.get(key, key)


def list_topics(
    category: str | None = None,
    difficulty: str | None = None,
    q: str | None = None,
    tag: str | None = None,
    limit: int | None = None,
) -> list[dict]:
    category_key = _key(category)
    difficulty_key = _difficulty_key(difficulty)
    query_key = _key(q)
    tag_key = _key(tag)

    results: list[dict] = []
    for topic in TOPICS:
        if not topic.get("is_active", True):
            continue
        if category_key and _key(topic["category"]) != category_key:
            continue
        if difficulty_key and _difficulty_key(topic["difficulty"]) != difficulty_key:
            continue
        topic_tags = [_key(item) for item in topic.get("tags", [])]
        if tag_key and tag_key not in topic_tags:
            continue
        if query_key:
            search_blob = " ".join(
                [
                    topic.get("title", ""),
                    topic.get("category", ""),
                    topic.get("description", ""),
                    " ".join(topic.get("tags", [])),
                ]
            )
            if query_key not in _key(search_blob):
                continue
        results.append(dict(topic))
        if limit and len(results) >= limit:
            break
    return results


def list_categories() -> list[dict]:
    counts = Counter(topic["category"] for topic in TOPICS if topic.get("is_active", True))
    return [
        {
            **category,
            "count": counts.get(category["name"], 0),
        }
        for category in TOPIC_CATEGORIES
    ]


def recommended_topics(
    difficulty: str | None = None,
    category: str | None = None,
    limit: int = 12,
) -> list[dict]:
    if category:
        return list_topics(category=category, difficulty=difficulty, limit=limit)

    difficulty_key = _difficulty_key(difficulty)
    preferred_categories = {
        "co ban": ["Xã hội", "Sức khỏe", "Văn hóa", "Giáo dục"],
        "trung cap": ["Giáo dục", "Công nghệ", "Xã hội", "Truyền thông"],
        "nang cao": ["Đạo đức", "Chính trị", "Kinh tế", "Công nghệ"],
    }.get(difficulty_key, [])

    candidates = list_topics(difficulty=difficulty)
    if preferred_categories:
        candidates.sort(
            key=lambda topic: preferred_categories.index(topic["category"])
            if topic["category"] in preferred_categories
            else len(preferred_categories)
        )
    return candidates[:limit]
