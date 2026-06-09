"""Curated local prompts for quick rebuttal practice."""

from __future__ import annotations


QUICK_REBUTTAL_PROMPTS = [{'id': 'qr_001',
  'topic_id': 'edu_ai_homework',
  'topic': 'Học sinh có nên được dùng AI để làm bài tập?',
  'category': 'Giáo dục',
  'difficulty': 'Trung cấp',
  'weak_argument': 'Học sinh nên được dùng AI để làm bài tập vì công nghệ này giúp các em hoàn thành mọi nhiệm vụ '
                   'nhanh hơn. Nếu AI có thể tạo ra câu trả lời đúng, việc học sinh tự làm từng bước trở nên không còn '
                   'cần thiết. Nhà trường nên chấp nhận điều này vì học sinh hiện nay cần tiết kiệm thời gian cho '
                   'nhiều hoạt động khác. Những lo ngại về gian lận không quá quan trọng, vì cuối cùng kết quả bài làm '
                   'mới là điều được chấm điểm. Hơn nữa, nhiều học sinh đã dùng AI nên cấm đoán chỉ làm các em tụt '
                   'hậu. Vì vậy, cho phép dùng AI làm bài tập là cách phù hợp nhất với giáo dục hiện đại.',
  'fallacy_hint': 'đánh đồng kết quả với quá trình học',
  'target_flaws': ['bỏ qua mục tiêu rèn kỹ năng', 'xem nhẹ gian lận học thuật', 'dựa vào số đông'],
  'expected_rebuttal_points': ['phân biệt AI hỗ trợ với AI làm thay',
                               'đánh giá cả quá trình học',
                               'đặt quy tắc sử dụng và khai báo rõ ràng']},
 {'id': 'qr_002',
  'topic_id': 'edu_phone_ban',
  'topic': 'Trường học có nên cấm điện thoại trong giờ học?',
  'category': 'Giáo dục',
  'difficulty': 'Cơ bản',
  'weak_argument': 'Trường học nên cấm hoàn toàn điện thoại trong giờ học vì điện thoại luôn làm học sinh mất tập '
                   'trung. Chỉ cần có điện thoại bên cạnh, học sinh chắc chắn sẽ lướt mạng xã hội hoặc chơi game thay '
                   'vì nghe giảng. Việc một số học sinh dùng điện thoại để tra cứu bài học không đủ để biện minh cho '
                   'rủi ro mà thiết bị này gây ra. Nếu nhà trường muốn cải thiện kết quả học tập, cách đơn giản nhất '
                   'là loại bỏ điện thoại khỏi lớp học. Phụ huynh cũng thường than phiền rằng con em mình nghiện điện '
                   'thoại, nên lệnh cấm là rất hợp lý. Vì vậy, cấm điện thoại sẽ gần như giải quyết được vấn đề mất '
                   'tập trung trong trường học.',
  'fallacy_hint': 'tuyệt đối hóa',
  'target_flaws': ['khẳng định điện thoại luôn gây mất tập trung',
                   'bỏ qua mục đích học tập',
                   'đơn giản hóa quan hệ nhân quả'],
  'expected_rebuttal_points': ['mức độ xao nhãng phụ thuộc cách dùng',
                               'có thể quản lý thay vì cấm tuyệt đối',
                               'cần dữ liệu về hiệu quả của lệnh cấm']},
 {'id': 'qr_003',
  'topic_id': 'edu_no_homework',
  'topic': 'Có nên bỏ bài tập về nhà?',
  'category': 'Giáo dục',
  'difficulty': 'Cơ bản',
  'weak_argument': 'Nên bỏ hoàn toàn bài tập về nhà vì học sinh đã học đủ nhiều ở trường. Sau nhiều giờ ngồi trong '
                   'lớp, việc tiếp tục làm bài ở nhà chỉ khiến các em thêm mệt mỏi và chán học. Nếu không còn bài tập '
                   'về nhà, học sinh chắc chắn sẽ có nhiều thời gian nghỉ ngơi hơn và học tập hiệu quả hơn vào ngày '
                   'hôm sau. Những giáo viên cho rằng bài tập giúp củng cố kiến thức đang quá coi trọng điểm số mà '
                   'quên mất sức khỏe tinh thần. Nhiều nước có nền giáo dục tốt cũng giảm bài tập, nên chúng ta nên '
                   'làm theo. Vì vậy, bỏ bài tập về nhà là giải pháp rõ ràng để học sinh hạnh phúc hơn.',
  'fallacy_hint': 'lưỡng phân giả',
  'target_flaws': ['đánh đồng mọi bài tập với quá tải',
                   'viện dẫn quốc gia khác thiếu bối cảnh',
                   'khẳng định chắc chắn thiếu bằng chứng'],
  'expected_rebuttal_points': ['phân biệt khối lượng và chất lượng bài tập',
                               'cân bằng củng cố kiến thức với nghỉ ngơi',
                               'xem xét độ tuổi và môn học']},
 {'id': 'qr_004',
  'topic_id': 'edu_grades_measure',
  'topic': 'Điểm số có còn là thước đo tốt cho năng lực học sinh?',
  'category': 'Giáo dục',
  'difficulty': 'Trung cấp',
  'weak_argument': 'Điểm số không còn là thước đo tốt cho năng lực học sinh vì có nhiều học sinh điểm cao nhưng vẫn '
                   'thiếu kỹ năng thực tế. Nếu điểm số không phản ánh đầy đủ sáng tạo, giao tiếp và tư duy phản biện, '
                   'thì nó gần như vô nghĩa trong giáo dục hiện đại. Nhà trường nên giảm mạnh vai trò của điểm số để '
                   'học sinh không còn áp lực thi cử. Những người bảo vệ điểm số thường chỉ muốn giữ cách đánh giá cũ '
                   'vì nó dễ quản lý hơn. Trong thực tế, năng lực thật sự phải được nhìn qua sản phẩm và thái độ học '
                   'tập chứ không phải vài con số. Vì vậy, điểm số nên được xem là một công cụ lỗi thời.',
  'fallacy_hint': 'khái quát hóa vội vàng',
  'target_flaws': ['từ hạn chế suy ra điểm số vô nghĩa',
                   'gán động cơ cho người ủng hộ',
                   'ép chọn giữa điểm số và kỹ năng'],
  'expected_rebuttal_points': ['điểm số vẫn đo được một phần năng lực',
                               'kết hợp nhiều hình thức đánh giá',
                               'cải thiện cách chấm thay vì loại bỏ']},
 {'id': 'qr_005',
  'topic_id': 'edu_critical_thinking_university',
  'topic': 'Đại học có nên bắt buộc học kỹ năng phản biện?',
  'category': 'Giáo dục',
  'difficulty': 'Trung cấp',
  'weak_argument': 'Đại học nên bắt buộc mọi sinh viên học kỹ năng phản biện vì đây là kỹ năng quan trọng nhất trong '
                   'thế kỷ hiện nay. Nếu sinh viên biết phản biện, họ chắc chắn sẽ học tốt hơn, làm việc tốt hơn và '
                   'tránh bị thao túng bởi thông tin sai lệch. Các môn chuyên ngành khác có thể khác nhau giữa từng '
                   'ngành, nhưng phản biện thì ai cũng cần nên phải được đặt làm môn bắt buộc. Việc một số sinh viên '
                   'không thích tranh luận không phải là lý do để bỏ qua kỹ năng này. Nhiều nhà tuyển dụng cũng thích '
                   'người có tư duy phản biện, nên đại học phải ưu tiên dạy nó ngay. Vì vậy, bắt buộc học phản biện là '
                   'cách tốt nhất để nâng chất lượng sinh viên.',
  'fallacy_hint': 'tuyệt đối hóa',
  'target_flaws': ['gọi đây là kỹ năng quan trọng nhất', 'cam kết kết quả chắc chắn', 'bỏ qua khác biệt chương trình'],
  'expected_rebuttal_points': ['chứng minh hiệu quả của môn bắt buộc',
                               'có thể tích hợp vào môn chuyên ngành',
                               'cân nhắc chi phí và chuẩn đầu ra']},
 {'id': 'qr_006',
  'topic_id': 'tech_ai_teacher',
  'topic': 'AI có nên thay thế một phần giáo viên?',
  'category': 'Công nghệ',
  'difficulty': 'Nâng cao',
  'weak_argument': 'AI nên thay thế một phần giáo viên vì máy móc có thể giảng bài nhanh, chính xác và không bị cảm '
                   'xúc chi phối. Khi học sinh cần giải thích bài tập, AI có thể trả lời ngay lập tức mà không phải '
                   'chờ giáo viên. Điều này chứng minh rằng nhiều nhiệm vụ giảng dạy truyền thống đã không còn cần con '
                   'người đảm nhiệm. Nếu trường học dùng AI nhiều hơn, chi phí giáo dục sẽ giảm và học sinh sẽ được hỗ '
                   'trợ liên tục. Những lo ngại về tương tác con người chỉ là cảm tính vì mục tiêu chính của giáo dục '
                   'là truyền đạt kiến thức. Vì vậy, AI nên thay thế giáo viên ở những phần có thể tự động hóa.',
  'fallacy_hint': 'giản lược hóa vai trò giáo viên',
  'target_flaws': ['đồng nhất giáo dục với truyền đạt kiến thức',
                   'bỏ qua sai lệch của AI',
                   'xem nhẹ tương tác và hỗ trợ cảm xúc'],
  'expected_rebuttal_points': ['AI phù hợp vai trò hỗ trợ hơn thay thế',
                               'giáo viên còn đánh giá và dẫn dắt',
                               'cần giám sát chất lượng và công bằng']},
 {'id': 'qr_007',
  'topic_id': 'tech_social_focus',
  'topic': 'Mạng xã hội có làm giảm khả năng tập trung?',
  'category': 'Công nghệ',
  'difficulty': 'Cơ bản',
  'weak_argument': 'Mạng xã hội chắc chắn làm giảm khả năng tập trung vì hầu hết người trẻ đều dành nhiều thời gian '
                   'lướt nội dung ngắn. Khi một người quen xem video liên tục, họ sẽ không còn kiên nhẫn đọc sách hoặc '
                   'nghe giảng lâu. Chỉ cần quan sát lớp học hiện nay cũng thấy học sinh dễ mất tập trung hơn trước '
                   'rất nhiều. Vì vậy, nguyên nhân chính của vấn đề tập trung chắc chắn là mạng xã hội. Những lợi ích '
                   'như kết nối bạn bè hay cập nhật tin tức không đáng kể so với tác hại này. Do đó, hạn chế mạng xã '
                   'hội là cách trực tiếp nhất để cải thiện khả năng tập trung.',
  'fallacy_hint': 'nhầm tương quan với nhân quả',
  'target_flaws': ['dựa vào quan sát lớp học', 'quy một nguyên nhân chính', 'xem nhẹ lợi ích mà không so sánh dữ liệu'],
  'expected_rebuttal_points': ['tách tác động của giấc ngủ và môi trường học',
                               'phân biệt loại nội dung và thời lượng dùng',
                               'cần nghiên cứu nhân quả']},
 {'id': 'qr_008',
  'topic_id': 'tech_tiktok_time_limit',
  'topic': 'Có nên giới hạn thời gian sử dụng TikTok ở thanh thiếu niên?',
  'category': 'Công nghệ',
  'difficulty': 'Trung cấp',
  'weak_argument': 'Nên giới hạn nghiêm ngặt thời gian sử dụng TikTok của thanh thiếu niên vì ứng dụng này là nguyên '
                   'nhân chính khiến các em học kém đi. Các video ngắn khiến não bộ quen với việc giải trí nhanh và '
                   'không còn muốn tiếp nhận kiến thức dài. Nếu thanh thiếu niên dùng TikTok ít hơn, điểm số của các '
                   'em chắc chắn sẽ cải thiện rõ rệt. Phụ huynh và giáo viên không cần xem xét quá nhiều yếu tố khác '
                   'như giấc ngủ, phương pháp học hay áp lực tâm lý. Nhiều người lớn đã thấy TikTok gây hại, nên việc '
                   'giới hạn là hoàn toàn hợp lý. Vì vậy, giới hạn TikTok nên là giải pháp trọng tâm để bảo vệ thanh '
                   'thiếu niên.',
  'fallacy_hint': 'nguyên nhân giả',
  'target_flaws': ['quy kết học kém chủ yếu cho TikTok',
                   'khẳng định điểm số chắc chắn tăng',
                   'bỏ qua nhiều yếu tố liên quan'],
  'expected_rebuttal_points': ['điểm số chịu tác động của nhiều nguyên nhân',
                               'đánh giá hiệu quả giới hạn theo dữ liệu',
                               'kết hợp kỹ năng tự quản lý']},
 {'id': 'qr_009',
  'topic_id': 'tech_personal_data_property',
  'topic': 'Dữ liệu cá nhân có nên được xem là tài sản riêng?',
  'category': 'Công nghệ',
  'difficulty': 'Nâng cao',
  'weak_argument': 'Dữ liệu cá nhân nên được xem là tài sản riêng vì nó thuộc về mỗi người giống như tiền bạc hay nhà '
                   'cửa. Nếu công ty muốn dùng dữ liệu của người dùng, họ phải trả tiền trực tiếp cho người đó. Cách '
                   'này chắc chắn sẽ khiến các nền tảng công nghệ tôn trọng quyền riêng tư hơn. Những khó khăn trong '
                   'việc định giá dữ liệu không quan trọng bằng nguyên tắc người dùng phải kiểm soát mọi thứ thuộc về '
                   'mình. Vì dữ liệu có thể tạo ra lợi nhuận, nên rõ ràng nó phải được đối xử như tài sản cá nhân. Do '
                   'đó, xem dữ liệu cá nhân là tài sản riêng sẽ giải quyết được vấn đề lạm dụng dữ liệu.',
  'fallacy_hint': 'so sánh khập khiễng',
  'target_flaws': ['đánh đồng dữ liệu với tài sản vật chất',
                   'coi định giá là vấn đề không đáng kể',
                   'hứa hẹn giải quyết hoàn toàn lạm dụng'],
  'expected_rebuttal_points': ['quyền riêng tư không nhất thiết đồng nghĩa quyền sở hữu',
                               'dữ liệu có thể được suy luận và dùng chung',
                               'cần cơ chế đồng ý và trách nhiệm pháp lý']},
 {'id': 'qr_010',
  'topic_id': 'tech_robot_eldercare',
  'topic': 'Robot có nên được dùng để chăm sóc người cao tuổi?',
  'category': 'Công nghệ',
  'difficulty': 'Trung cấp',
  'weak_argument': 'Robot nên được dùng rộng rãi để chăm sóc người cao tuổi vì máy móc có thể làm việc liên tục và '
                   'không biết mệt. Khi có robot nhắc uống thuốc, theo dõi sức khỏe và hỗ trợ sinh hoạt, người cao '
                   'tuổi chắc chắn sẽ được chăm sóc tốt hơn. Nhiều gia đình hiện nay bận rộn, nên thay thế một phần '
                   'vai trò chăm sóc bằng robot là lựa chọn hợp lý nhất. Những lo ngại về cảm xúc hay sự cô đơn không '
                   'quá quan trọng vì điều người cao tuổi cần nhất là an toàn và đúng giờ. Nếu công nghệ đã làm được '
                   'thì con người không nên giữ cách chăm sóc truyền thống quá lâu. Vì vậy, đầu tư robot chăm sóc nên '
                   'được ưu tiên hơn các mô hình chăm sóc cũ.',
  'fallacy_hint': 'sùng bái giải pháp công nghệ',
  'target_flaws': ['đồng nhất an toàn với chăm sóc tốt',
                   'xem nhẹ cô đơn và phẩm giá',
                   'đặt robot đối lập với mô hình con người'],
  'expected_rebuttal_points': ['robot nên bổ trợ người chăm sóc',
                               'người cao tuổi cần quyền lựa chọn',
                               'phải kiểm soát lỗi kỹ thuật và dữ liệu']},
 {'id': 'qr_011',
  'topic_id': 'soc_cyberbullying_penalty',
  'topic': 'Có nên phạt nặng hành vi bắt nạt trên mạng?',
  'category': 'Xã hội',
  'difficulty': 'Trung cấp',
  'weak_argument': 'Nên phạt thật nặng mọi hành vi bắt nạt trên mạng vì chỉ có hình phạt nghiêm khắc mới làm người ta '
                   'sợ. Nếu người dùng biết mình có thể bị xử lý nặng, họ chắc chắn sẽ không dám xúc phạm người khác '
                   'nữa. Những biện pháp giáo dục hay nhắc nhở thường quá nhẹ và không đủ sức răn đe. Bắt nạt trên '
                   'mạng gây tổn thương tinh thần nghiêm trọng, nên bất kỳ hành vi nào cũng cần bị trừng phạt mạnh. '
                   'Việc phân biệt mức độ nặng nhẹ chỉ làm quá trình xử lý chậm hơn. Vì vậy, tăng hình phạt là cách '
                   'hiệu quả nhất để chấm dứt bắt nạt trên mạng.',
  'fallacy_hint': 'đánh đồng trừng phạt với răn đe',
  'target_flaws': ['giả định phạt nặng chắc chắn ngăn vi phạm',
                   'không phân biệt mức độ',
                   'loại bỏ giáo dục và phục hồi'],
  'expected_rebuttal_points': ['chế tài cần tương xứng hành vi',
                               'kết hợp giáo dục và cơ chế báo cáo',
                               'đánh giá bằng chứng về hiệu quả răn đe']},
 {'id': 'qr_012',
  'topic_id': 'soc_young_independent',
  'topic': 'Người trẻ có nên sống tự lập sớm?',
  'category': 'Xã hội',
  'difficulty': 'Cơ bản',
  'weak_argument': 'Người trẻ nên sống tự lập sớm vì chỉ khi rời khỏi gia đình họ mới thật sự trưởng thành. Nếu cứ '
                   'sống cùng cha mẹ, người trẻ sẽ dễ phụ thuộc và không biết tự chịu trách nhiệm. Việc tự trả tiền '
                   'nhà, tự nấu ăn và tự giải quyết vấn đề chắc chắn sẽ giúp họ mạnh mẽ hơn. Những khó khăn về tài '
                   'chính chỉ là thử thách cần vượt qua chứ không nên là lý do trì hoãn. Nhiều người thành công đều '
                   'từng tự lập từ sớm, nên đây là con đường đáng khuyến khích. Vì vậy, người trẻ nên rời gia đình '
                   'càng sớm càng tốt để trưởng thành nhanh hơn.',
  'fallacy_hint': 'khái quát hóa từ người thành công',
  'target_flaws': ['đồng nhất rời nhà với trưởng thành', 'bỏ qua điều kiện tài chính', 'thiên lệch sống sót'],
  'expected_rebuttal_points': ['tự lập có nhiều hình thức',
                               'thời điểm phụ thuộc nguồn lực và văn hóa',
                               'chuẩn bị kỹ năng quan trọng hơn rời nhà sớm']},
 {'id': 'qr_013',
  'topic_id': 'soc_remote_work',
  'topic': 'Làm việc từ xa có tốt hơn làm việc tại văn phòng?',
  'category': 'Xã hội',
  'difficulty': 'Trung cấp',
  'weak_argument': 'Làm việc từ xa tốt hơn làm việc tại văn phòng vì nhân viên có thể ở nhà thoải mái và tiết kiệm '
                   'thời gian di chuyển. Khi không phải đến công ty, họ sẽ có nhiều năng lượng hơn để tập trung vào '
                   'công việc. Điều này cho thấy làm việc từ xa chắc chắn giúp năng suất tăng lên. Những vấn đề như '
                   'giao tiếp nhóm hay kỷ luật cá nhân có thể tự giải quyết bằng các công cụ trực tuyến. Văn phòng '
                   'truyền thống chỉ phù hợp với thời kỳ cũ khi công nghệ chưa phát triển. Vì vậy, doanh nghiệp nên '
                   'chuyển sang làm việc từ xa càng nhiều càng tốt.',
  'fallacy_hint': 'khái quát hóa vội vàng',
  'target_flaws': ['suy từ thoải mái sang năng suất',
                   'bỏ qua khác biệt công việc',
                   'cho rằng công cụ giải quyết mọi vấn đề nhóm'],
  'expected_rebuttal_points': ['hiệu quả phụ thuộc vai trò và cá nhân',
                               'mô hình kết hợp có thể phù hợp hơn',
                               'cần đo năng suất và sức khỏe dài hạn']},
 {'id': 'qr_014',
  'topic_id': 'soc_public_transport',
  'topic': 'Có nên khuyến khích giao thông công cộng hơn xe cá nhân?',
  'category': 'Xã hội',
  'difficulty': 'Trung cấp',
  'weak_argument': 'Nên khuyến khích giao thông công cộng hơn xe cá nhân vì xe buýt và tàu điện có thể chở nhiều người '
                   'cùng lúc. Nếu nhiều người bỏ xe cá nhân, đường phố chắc chắn sẽ hết kẹt xe và ô nhiễm sẽ giảm '
                   'mạnh. Những bất tiện như chờ lâu, thiếu tuyến hoặc đông đúc chỉ là vấn đề nhỏ so với lợi ích '
                   'chung. Người dân nên thay đổi thói quen cá nhân để phù hợp với hướng phát triển của thành phố. '
                   'Nhiều nước phát triển dùng giao thông công cộng hiệu quả, nên chúng ta cũng nên đi theo con đường '
                   'đó. Vì vậy, giao thông công cộng nên được ưu tiên rõ ràng hơn xe cá nhân.',
  'fallacy_hint': 'đơn giản hóa quan hệ nhân quả',
  'target_flaws': ['cam kết hết kẹt xe', 'xem nhẹ chất lượng hạ tầng', 'viện dẫn nước khác thiếu bối cảnh'],
  'expected_rebuttal_points': ['phải tăng độ phủ và độ tin cậy',
                               'không phải mọi chuyến đi đều thay thế được',
                               'cần chính sách chuyển đổi công bằng']},
 {'id': 'qr_015',
  'topic_id': 'soc_celeb_role_model',
  'topic': 'Người nổi tiếng có trách nhiệm làm gương không?',
  'category': 'Xã hội',
  'difficulty': 'Cơ bản',
  'weak_argument': 'Người nổi tiếng chắc chắn có trách nhiệm làm gương vì họ có nhiều người theo dõi và ảnh hưởng đến '
                   'công chúng. Khi một ca sĩ, diễn viên hay influencer cư xử sai, người trẻ có thể bắt chước hành vi '
                   'đó. Vì vậy, mọi người nổi tiếng phải luôn giữ hình ảnh chuẩn mực cả trong công việc lẫn đời sống '
                   'cá nhân. Việc nói rằng họ cũng là người bình thường không đủ để miễn trách nhiệm xã hội cho họ. '
                   'Nếu đã nhận lợi ích từ sự chú ý của công chúng, họ phải chấp nhận bị đánh giá nghiêm khắc hơn. Do '
                   'đó, người nổi tiếng không có quyền sống tùy ý như người bình thường.',
  'fallacy_hint': 'mở rộng trách nhiệm quá mức',
  'target_flaws': ['giả định công chúng luôn bắt chước',
                   'xóa ranh giới đời tư',
                   'đánh đồng ảnh hưởng với nghĩa vụ hoàn hảo'],
  'expected_rebuttal_points': ['trách nhiệm nên gắn với hành vi công khai và quảng bá',
                               'phân biệt sai phạm với lựa chọn riêng tư',
                               'gia đình và nền tảng cũng có vai trò']},
 {'id': 'qr_016',
  'topic_id': 'eco_personal_finance_school',
  'topic': 'Có nên dạy quản lý tài chính cá nhân từ cấp 3?',
  'category': 'Kinh tế',
  'difficulty': 'Cơ bản',
  'weak_argument': 'Nên dạy quản lý tài chính cá nhân từ cấp 3 vì học sinh sắp bước vào giai đoạn tự quyết định chi '
                   'tiêu. Nếu các em biết tiết kiệm, lập ngân sách và tránh nợ xấu, tương lai tài chính chắc chắn sẽ '
                   'ổn định hơn. Những môn học truyền thống như lịch sử hay địa lý không giúp học sinh xử lý tiền bạc '
                   'hằng ngày nhiều bằng kỹ năng tài chính. Vì vậy, nhà trường nên ưu tiên môn này trong chương trình '
                   'chính khóa. Nhiều người trẻ chi tiêu thiếu kiểm soát chỉ vì trước đây không được dạy về tiền. Do '
                   'đó, dạy tài chính cá nhân từ cấp 3 sẽ giải quyết được phần lớn vấn đề tài chính của người trẻ.',
  'fallacy_hint': 'hứa hẹn quá mức',
  'target_flaws': ['coi thiếu môn học là nguyên nhân chính',
                   'hạ thấp môn học khác',
                   'khẳng định giải quyết phần lớn vấn đề'],
  'expected_rebuttal_points': ['môn tài chính hữu ích nhưng không bảo đảm hành vi',
                               'chất lượng dạy và hoàn cảnh thu nhập đều quan trọng',
                               'có thể tích hợp thay vì thay thế môn khác']},
 {'id': 'qr_017',
  'topic_id': 'eco_online_spending',
  'topic': 'Mua sắm online có làm người trẻ chi tiêu mất kiểm soát?',
  'category': 'Kinh tế',
  'difficulty': 'Cơ bản',
  'weak_argument': 'Mua sắm online rõ ràng làm người trẻ chi tiêu mất kiểm soát vì chỉ cần vài cú nhấp là có thể đặt '
                   'hàng. Các chương trình giảm giá, miễn phí vận chuyển và livestream bán hàng khiến người trẻ rất '
                   'khó cưỡng lại. Nếu không có mua sắm online, họ chắc chắn sẽ tiết kiệm được nhiều tiền hơn. Việc '
                   'một số người vẫn chi tiêu hợp lý không thay đổi thực tế rằng nền tảng online được thiết kế để kích '
                   'thích mua sắm. Nhiều bạn trẻ than hết tiền sau các đợt sale, nên nguyên nhân chính là thương mại '
                   'điện tử. Vì vậy, mua sắm online nên bị kiểm soát chặt hơn để bảo vệ người trẻ.',
  'fallacy_hint': 'nguyên nhân đơn nhất',
  'target_flaws': ['quy toàn bộ mất kiểm soát cho nền tảng',
                   'dựa vào lời than sau đợt sale',
                   'bỏ qua năng lực tự quản lý'],
  'expected_rebuttal_points': ['thiết kế nền tảng chỉ là một yếu tố',
                               'cần dữ liệu so sánh hành vi chi tiêu',
                               'kết hợp công cụ giới hạn và giáo dục tài chính']},
 {'id': 'qr_018',
  'topic_id': 'eco_green_tax',
  'topic': 'Có nên đánh thuế cao hơn với sản phẩm gây hại môi trường?',
  'category': 'Kinh tế',
  'difficulty': 'Nâng cao',
  'weak_argument': 'Nên đánh thuế cao hơn với sản phẩm gây hại môi trường vì giá cao sẽ khiến người tiêu dùng tự động '
                   'mua ít lại. Khi các sản phẩm ô nhiễm trở nên đắt hơn, doanh nghiệp chắc chắn sẽ chuyển sang sản '
                   'xuất xanh. Đây là cách đơn giản nhất để giải quyết vấn đề môi trường mà không cần thay đổi hành vi '
                   'quá phức tạp. Những lo ngại về người thu nhập thấp không nên cản trở mục tiêu bảo vệ môi trường. '
                   'Nếu một sản phẩm gây hại, người dùng phải trả giá cao hơn cho tác động của nó. Vì vậy, tăng thuế '
                   'là công cụ hiệu quả nhất để giảm ô nhiễm.',
  'fallacy_hint': 'đơn giản hóa tác động kinh tế',
  'target_flaws': ['giả định giá cao luôn giảm mua', 'bỏ qua tác động lũy thoái', 'gọi thuế là công cụ hiệu quả nhất'],
  'expected_rebuttal_points': ['thiết kế thuế cần hoàn trả cho nhóm thu nhập thấp',
                               'phải có sản phẩm thay thế',
                               'kết hợp tiêu chuẩn và đầu tư xanh']},
 {'id': 'qr_019',
  'topic_id': 'eco_startup_university',
  'topic': 'Startup có nên được ưu tiên hỗ trợ trong trường đại học?',
  'category': 'Kinh tế',
  'difficulty': 'Trung cấp',
  'weak_argument': 'Startup nên được ưu tiên hỗ trợ trong trường đại học vì khởi nghiệp là con đường nhanh nhất để '
                   'sinh viên tạo ra giá trị thực tế. Nếu trường đại học có nhiều chương trình ươm tạo, sinh viên chắc '
                   'chắn sẽ năng động và sáng tạo hơn. Những hoạt động học thuật truyền thống đôi khi quá chậm so với '
                   'nhu cầu thị trường. Vì vậy, nhà trường nên dành nhiều nguồn lực hơn cho startup thay vì chỉ tập '
                   'trung nghiên cứu và lý thuyết. Nhiều doanh nhân thành công bắt đầu từ khi còn rất trẻ, nên sinh '
                   'viên nên được khuyến khích thử sớm. Do đó, ưu tiên startup là cách tốt nhất để đại học trở nên '
                   'thực tiễn hơn.',
  'fallacy_hint': 'thiên lệch sống sót',
  'target_flaws': ['coi khởi nghiệp là đường nhanh nhất',
                   'đặt startup đối lập nghiên cứu',
                   'dựa vào doanh nhân thành công'],
  'expected_rebuttal_points': ['hỗ trợ startup nhưng không lấn át sứ mệnh học thuật',
                               'tính cả tỷ lệ thất bại và rủi ro',
                               'đánh giá nhu cầu theo ngành']},
 {'id': 'qr_020',
  'topic_id': 'eco_minimum_wage_yearly',
  'topic': 'Lương tối thiểu có nên tăng hằng năm?',
  'category': 'Kinh tế',
  'difficulty': 'Nâng cao',
  'weak_argument': 'Lương tối thiểu nên tăng hằng năm vì chi phí sinh hoạt luôn tăng và người lao động cần được bảo '
                   'vệ. Nếu mức lương không tăng đều, người lao động chắc chắn sẽ ngày càng khó sống hơn. Doanh nghiệp '
                   'có thể điều chỉnh chi phí hoặc tăng giá sản phẩm để thích nghi với chính sách này. Những lo ngại '
                   'về thất nghiệp thường bị phóng đại vì công ty vẫn cần nhân viên để hoạt động. Khi người lao động '
                   'có nhiều tiền hơn, họ sẽ tiêu dùng nhiều hơn và nền kinh tế sẽ tốt hơn. Vì vậy, tăng lương tối '
                   'thiểu hằng năm là lựa chọn hợp lý nhất.',
  'fallacy_hint': 'khái quát hóa chính sách',
  'target_flaws': ['bỏ qua khác biệt thị trường lao động',
                   'xem nhẹ rủi ro thất nghiệp',
                   'ấn định tăng hằng năm thiếu tiêu chí'],
  'expected_rebuttal_points': ['gắn điều chỉnh với lạm phát và năng suất',
                               'xem xét vùng và ngành',
                               'kết hợp hỗ trợ doanh nghiệp và người lao động']},
 {'id': 'qr_021',
  'topic_id': 'eth_ai_writing_cheating',
  'topic': 'Dùng AI viết bài có phải là gian lận không?',
  'category': 'Đạo đức',
  'difficulty': 'Trung cấp',
  'weak_argument': 'Dùng AI viết bài chắc chắn là gian lận vì học sinh không tự tạo ra toàn bộ nội dung bằng năng lực '
                   'của mình. Nếu một bài viết được AI hỗ trợ, giáo viên không thể biết đâu là suy nghĩ thật của học '
                   'sinh. Vì vậy, mọi hình thức dùng AI trong bài viết nên bị xem là vi phạm học thuật. Việc nói AI '
                   'chỉ hỗ trợ ý tưởng là cách biện minh nguy hiểm cho thói quen phụ thuộc. Nếu cho phép dùng AI một '
                   'chút, học sinh sẽ dần để AI làm hết mọi thứ. Do đó, cấm AI trong viết bài là cách duy nhất để bảo '
                   'vệ sự trung thực.',
  'fallacy_hint': 'lưỡng phân giả',
  'target_flaws': ['đánh đồng mọi hỗ trợ AI với gian lận',
                   'trượt dốc từ dùng ít đến làm thay',
                   'coi cấm hoàn toàn là cách duy nhất'],
  'expected_rebuttal_points': ['phân loại mức hỗ trợ được phép',
                               'yêu cầu khai báo và kiểm chứng',
                               'thiết kế bài đánh giá đo được tư duy cá nhân']},
 {'id': 'qr_022',
  'topic_id': 'eth_ai_camera_school',
  'topic': 'Có nên sử dụng camera AI để giám sát học sinh?',
  'category': 'Đạo đức',
  'difficulty': 'Nâng cao',
  'weak_argument': 'Nên sử dụng camera AI để giám sát học sinh vì công nghệ này có thể phát hiện hành vi bất thường '
                   'nhanh hơn con người. Nếu hệ thống nhận diện được đánh nhau, gian lận hoặc bỏ lớp, nhà trường chắc '
                   'chắn sẽ quản lý học sinh tốt hơn. Quyền riêng tư trong trường học không nên được đặt cao hơn sự an '
                   'toàn và kỷ luật. Học sinh ngoan sẽ không có gì phải lo lắng khi bị camera theo dõi. Những phản đối '
                   'về lạm dụng dữ liệu chỉ làm chậm quá trình hiện đại hóa quản lý giáo dục. Vì vậy, camera AI nên '
                   'được triển khai rộng rãi trong trường học.',
  'fallacy_hint': 'lập luận không có gì phải giấu',
  'target_flaws': ['xem nhẹ quyền riêng tư', 'giả định nhận diện luôn chính xác', 'bỏ qua nguy cơ lạm dụng dữ liệu'],
  'expected_rebuttal_points': ['chứng minh tính cần thiết và tương xứng',
                               'đánh giá sai số và thiên lệch',
                               'giới hạn lưu trữ cùng giám sát con người']},
 {'id': 'qr_023',
  'topic_id': 'eth_public_grades',
  'topic': 'Có nên công khai điểm số của học sinh trong lớp?',
  'category': 'Đạo đức',
  'difficulty': 'Cơ bản',
  'weak_argument': 'Nên công khai điểm số trong lớp vì điều này tạo động lực để học sinh cố gắng hơn. Khi thấy bạn bè '
                   'đạt điểm cao, học sinh điểm thấp sẽ tự biết mình cần nỗ lực. Sự cạnh tranh công khai luôn giúp lớp '
                   'học tiến bộ nhanh hơn so với việc giữ điểm riêng tư. Những học sinh cảm thấy xấu hổ nên xem đó là '
                   'động lực thay vì áp lực tiêu cực. Giáo viên cũng dễ khen thưởng và nhắc nhở khi mọi người đều biết '
                   'kết quả của nhau. Vì vậy, công khai điểm số là cách đơn giản để nâng cao thành tích lớp học.',
  'fallacy_hint': 'đánh đồng xấu hổ với động lực',
  'target_flaws': ['coi cạnh tranh luôn có lợi', 'xem nhẹ quyền riêng tư', 'bỏ qua tác động tâm lý khác nhau'],
  'expected_rebuttal_points': ['phản hồi riêng tư vẫn tạo động lực',
                               'so sánh công khai có thể làm giảm học tập',
                               'cần đồng thuận và bảo vệ học sinh yếu thế']},
 {'id': 'qr_024',
  'topic_id': 'eth_ai_hiring',
  'topic': 'AI có nên được quyền đưa ra quyết định tuyển dụng?',
  'category': 'Đạo đức',
  'difficulty': 'Nâng cao',
  'weak_argument': 'AI nên được quyền đưa ra quyết định tuyển dụng vì máy móc có thể xử lý hồ sơ nhanh và khách quan '
                   'hơn con người. Nếu thuật toán dựa trên dữ liệu, nó sẽ ít bị cảm xúc hoặc thiên vị cá nhân ảnh '
                   'hưởng. Doanh nghiệp dùng AI tuyển dụng chắc chắn sẽ tiết kiệm thời gian và chọn được ứng viên phù '
                   'hợp hơn. Những lo ngại về dữ liệu thiên lệch không quá nghiêm trọng vì hệ thống có thể được cập '
                   'nhật dần. Con người thường đánh giá ứng viên theo cảm tính, nên để AI quyết định sẽ công bằng hơn. '
                   'Vì vậy, AI nên được trao vai trò chính trong tuyển dụng.',
  'fallacy_hint': 'thiên kiến tự động hóa',
  'target_flaws': ['đồng nhất dữ liệu với khách quan',
                   'xem nhẹ dữ liệu thiên lệch',
                   'giao quyết định chính cho hệ thống khó giải thích'],
  'expected_rebuttal_points': ['AI có thể kế thừa phân biệt đối xử',
                               'cần người chịu trách nhiệm và cơ chế khiếu nại',
                               'dùng AI hỗ trợ sàng lọc có kiểm toán']},
 {'id': 'qr_025',
  'topic_id': 'eth_cancel_scandal',
  'topic': 'Có nên tha thứ cho người nổi tiếng sau scandal?',
  'category': 'Đạo đức',
  'difficulty': 'Trung cấp',
  'weak_argument': 'Nên tha thứ cho người nổi tiếng sau scandal vì ai cũng có thể mắc sai lầm trong cuộc sống. Nếu một '
                   'người đã xin lỗi công khai, xã hội nên cho họ cơ hội quay lại thay vì tiếp tục chỉ trích. Việc giữ '
                   'mãi lỗi lầm cũ chỉ làm môi trường mạng trở nên độc hại và thiếu nhân văn. Những người phản đối tha '
                   'thứ thường quá khắt khe và quên rằng bản thân họ cũng không hoàn hảo. Khi người nổi tiếng có tài '
                   'năng, công chúng không nên để một scandal phá hủy toàn bộ sự nghiệp của họ. Vì vậy, tha thứ sau '
                   'scandal là lựa chọn văn minh hơn.',
  'fallacy_hint': 'đơn giản hóa trách nhiệm',
  'target_flaws': ['coi lời xin lỗi là đủ',
                   'tấn công người phản đối là quá khắt khe',
                   'dùng tài năng để giảm nhẹ hậu quả'],
  'expected_rebuttal_points': ['mức độ tha thứ phụ thuộc tính chất sai phạm',
                               'cần hành động khắc phục chứ không chỉ xin lỗi',
                               'cơ hội quay lại nên đi cùng trách nhiệm']},
 {'id': 'qr_026',
  'topic_id': 'pol_student_policy_voice',
  'topic': 'Có nên cho học sinh tham gia góp ý chính sách giáo dục?',
  'category': 'Chính trị',
  'difficulty': 'Trung cấp',
  'weak_argument': 'Nên cho học sinh tham gia góp ý chính sách giáo dục vì các em là người trực tiếp chịu ảnh hưởng từ '
                   'trường học. Nếu học sinh được nói lên ý kiến, chính sách chắc chắn sẽ thực tế và gần với nhu cầu '
                   'hơn. Người lớn đôi khi không hiểu hết áp lực học tập hiện nay, nên ý kiến học sinh phải được ưu '
                   'tiên. Những lo ngại rằng học sinh còn thiếu kinh nghiệm không nên ngăn các em tham gia quyết định. '
                   'Nếu chính sách dành cho học sinh mà không hỏi học sinh, chính sách đó khó có thể đúng. Vì vậy, học '
                   'sinh nên có tiếng nói quan trọng trong mọi thay đổi giáo dục.',
  'fallacy_hint': 'đánh đồng trải nghiệm với chuyên môn',
  'target_flaws': ['khẳng định ý kiến học sinh phải được ưu tiên',
                   'xem nhẹ hạn chế kinh nghiệm',
                   'mở rộng thành mọi thay đổi giáo dục'],
  'expected_rebuttal_points': ['học sinh cần được tham vấn có cấu trúc',
                               'quyết định nên kết hợp nhiều bên',
                               'đại diện phải đa dạng và có thông tin']},
 {'id': 'qr_027',
  'topic_id': 'pol_digital_media_literacy',
  'topic': 'Có nên bắt buộc công dân học kỹ năng truyền thông số?',
  'category': 'Chính trị',
  'difficulty': 'Trung cấp',
  'weak_argument': 'Nên bắt buộc công dân học kỹ năng truyền thông số vì hiện nay hầu hết vấn đề xã hội đều bắt nguồn '
                   'từ việc dùng mạng sai cách. Nếu mọi người biết kiểm chứng thông tin, cư xử văn minh và bảo vệ dữ '
                   'liệu cá nhân, môi trường mạng chắc chắn sẽ tốt hơn. Các chương trình tự nguyện thường không đủ vì '
                   'người thiếu kỹ năng lại là người ít chủ động học nhất. Do đó, nhà nước cần bắt buộc để đảm bảo ai '
                   'cũng đạt mức hiểu biết tối thiểu. Những người phản đối bắt buộc học chỉ đang xem nhẹ nguy cơ của '
                   'tin giả và lừa đảo trực tuyến. Vì vậy, kỹ năng truyền thông số nên trở thành yêu cầu bắt buộc với '
                   'mọi công dân.',
  'fallacy_hint': 'khái quát hóa nguyên nhân',
  'target_flaws': ['quy hầu hết vấn đề xã hội cho dùng mạng',
                   'giả định bắt buộc sẽ hiệu quả',
                   'gán động cơ cho người phản đối'],
  'expected_rebuttal_points': ['xác định chuẩn kỹ năng và cách đánh giá',
                               'bảo đảm khả năng tiếp cận cho mọi nhóm',
                               'so sánh bắt buộc với khuyến khích và hỗ trợ']},
 {'id': 'qr_028',
  'topic_id': 'pol_fake_news_control',
  'topic': 'Có nên siết chặt quản lý tin giả trên mạng xã hội?',
  'category': 'Chính trị',
  'difficulty': 'Nâng cao',
  'weak_argument': 'Nên siết chặt quản lý tin giả trên mạng xã hội vì tin giả có thể gây hoang mang và làm xã hội mất '
                   'niềm tin. Nếu nhà nước kiểm soát mạnh hơn, người dùng chắc chắn sẽ tiếp cận thông tin chính xác '
                   'hơn. Các nền tảng không thể tự quản lý hiệu quả vì họ chỉ quan tâm đến lượt xem và lợi nhuận. '
                   'Những lo ngại về tự do ngôn luận không quan trọng bằng việc bảo vệ cộng đồng khỏi thông tin sai. '
                   'Nếu một nội dung có nguy cơ gây hiểu lầm, tốt nhất là nên gỡ bỏ ngay. Vì vậy, quản lý tin giả càng '
                   'chặt thì môi trường mạng càng lành mạnh.',
  'fallacy_hint': 'lưỡng phân giả giữa an toàn và tự do',
  'target_flaws': ['coi kiểm soát mạnh luôn tăng độ chính xác',
                   'gỡ nội dung chỉ vì có nguy cơ',
                   'bỏ qua sai sót và lạm quyền'],
  'expected_rebuttal_points': ['cần tiêu chí minh bạch và quy trình kháng nghị',
                               'ưu tiên đính chính hoặc gắn nhãn khi phù hợp',
                               'có giám sát độc lập để bảo vệ tự do biểu đạt']},
 {'id': 'qr_029',
  'topic_id': 'pol_ai_public_service',
  'topic': 'Chính phủ có nên dùng AI trong dịch vụ công?',
  'category': 'Chính trị',
  'difficulty': 'Nâng cao',
  'weak_argument': 'Chính phủ nên dùng AI trong dịch vụ công vì công nghệ này có thể xử lý hồ sơ nhanh và giảm tình '
                   'trạng chờ đợi. Khi người dân được hỗ trợ bởi chatbot hoặc hệ thống tự động, thủ tục hành chính '
                   'chắc chắn sẽ thuận tiện hơn. Máy móc không mệt mỏi và không thiên vị, nên dịch vụ công sẽ công '
                   'bằng hơn nếu dùng AI. Những lo ngại về sai sót có thể bỏ qua vì con người cũng thường mắc lỗi '
                   'trong quá trình xử lý hồ sơ. Nếu khu vực tư nhân đã dùng AI hiệu quả, chính phủ cũng nên áp dụng '
                   'mạnh mẽ. Vì vậy, AI nên trở thành công cụ trung tâm trong dịch vụ công.',
  'fallacy_hint': 'thiên kiến tự động hóa',
  'target_flaws': ['cho rằng máy không thiên vị', 'xem nhẹ sai sót ở dịch vụ công', 'suy từ khu vực tư sang chính phủ'],
  'expected_rebuttal_points': ['quyết định hệ trọng cần người xem xét',
                               'kiểm toán thiên lệch và bảo mật',
                               'duy trì kênh phục vụ người khó tiếp cận số']},
 {'id': 'qr_030',
  'topic_id': 'pol_digital_citizenship_school',
  'topic': 'Có nên mở rộng giáo dục công dân số trong nhà trường?',
  'category': 'Chính trị',
  'difficulty': 'Cơ bản',
  'weak_argument': 'Nên mở rộng giáo dục công dân số trong nhà trường vì học sinh hiện nay sống gần như mỗi ngày trên '
                   'Internet. Nếu các em được học cách cư xử, kiểm chứng thông tin và bảo vệ dữ liệu, các vấn đề trên '
                   'mạng chắc chắn sẽ giảm mạnh. Những môn học truyền thống không còn đủ để chuẩn bị cho đời sống số '
                   'hiện đại. Nhà trường cần ưu tiên công dân số vì mạng xã hội ảnh hưởng trực tiếp đến suy nghĩ và '
                   'hành vi của học sinh. Việc thêm nội dung này vào chương trình không nên bị xem là quá tải, vì đây '
                   'là kỹ năng thiết yếu. Vì vậy, giáo dục công dân số nên được mở rộng càng sớm càng tốt.',
  'fallacy_hint': 'hứa hẹn quá mức',
  'target_flaws': ['khẳng định vấn đề mạng chắc chắn giảm mạnh',
                   'coi môn truyền thống không còn đủ',
                   'xem nhẹ quá tải chương trình'],
  'expected_rebuttal_points': ['tích hợp nội dung theo lứa tuổi',
                               'đào tạo giáo viên và đo hiệu quả',
                               'coi đây là bổ sung chứ không thay thế nền tảng khác']},
 {'id': 'qr_031',
  'topic_id': 'env_plastic_bag_ban',
  'topic': 'Có nên cấm túi nilon dùng một lần?',
  'category': 'Môi trường',
  'difficulty': 'Cơ bản',
  'weak_argument': 'Nên cấm túi nilon dùng một lần vì đây là một trong những nguyên nhân rõ ràng nhất gây ô nhiễm môi '
                   'trường. Nếu không còn túi nilon, người dân chắc chắn sẽ chuyển sang các lựa chọn thân thiện hơn '
                   'như túi vải hoặc túi giấy. Những bất tiện trong mua sắm chỉ là vấn đề nhỏ so với lợi ích bảo vệ '
                   'môi trường. Doanh nghiệp và người tiêu dùng sẽ tự thích nghi khi lệnh cấm được áp dụng đủ nghiêm. '
                   'Nhiều quốc gia đã hạn chế túi nilon, nên chúng ta cũng nên làm theo ngay. Vì vậy, cấm túi nilon '
                   'dùng một lần là giải pháp đơn giản và hiệu quả.',
  'fallacy_hint': 'giải pháp đơn nhất',
  'target_flaws': ['giả định người dân tự chuyển sang lựa chọn tốt',
                   'dựa vào việc nước khác đã làm',
                   'bỏ qua tác động của vật liệu thay thế'],
  'expected_rebuttal_points': ['so sánh vòng đời các lựa chọn thay thế',
                               'thiết kế lộ trình và ngoại lệ cần thiết',
                               'kết hợp tái sử dụng và hạ tầng xử lý']},
 {'id': 'qr_032',
  'topic_id': 'env_school_recycling',
  'topic': 'Trường học có nên bắt buộc phân loại rác?',
  'category': 'Môi trường',
  'difficulty': 'Cơ bản',
  'weak_argument': 'Trường học nên bắt buộc phân loại rác vì học sinh cần được rèn thói quen bảo vệ môi trường từ nhỏ. '
                   'Nếu các em phân loại rác mỗi ngày, chắc chắn sau này các em sẽ trở thành công dân có ý thức hơn. '
                   'Việc bắt buộc là cần thiết vì nếu chỉ khuyến khích thì học sinh thường sẽ không tự giác làm. Những '
                   'khó khăn như thiếu thùng rác riêng hay quy trình xử lý sau phân loại không phải là vấn đề lớn. '
                   'Quan trọng nhất là tạo thói quen, còn hệ thống xử lý có thể hoàn thiện dần. Vì vậy, phân loại rác '
                   'bắt buộc trong trường học là bước đi đúng đắn.',
  'fallacy_hint': 'đánh đồng hành vi với kết quả',
  'target_flaws': ['bảo đảm thói quen tương lai',
                   'xem nhẹ khâu xử lý sau phân loại',
                   'coi bắt buộc luôn tốt hơn khuyến khích'],
  'expected_rebuttal_points': ['cần hệ thống thu gom xử lý đồng bộ',
                               'đủ thùng rác và hướng dẫn rõ ràng',
                               'đo chất lượng phân loại thay vì chỉ bắt buộc']},
 {'id': 'qr_033',
  'topic_id': 'env_gas_car_limit',
  'topic': 'Có nên hạn chế xe xăng trong thành phố lớn?',
  'category': 'Môi trường',
  'difficulty': 'Nâng cao',
  'weak_argument': 'Nên hạn chế xe xăng trong thành phố lớn vì xe xăng là nguyên nhân chính gây ô nhiễm không khí đô '
                   'thị. Nếu người dân chuyển sang xe điện hoặc phương tiện công cộng, chất lượng không khí chắc chắn '
                   'sẽ cải thiện nhanh chóng. Những lo ngại về chi phí mua xe mới chỉ là khó khăn ban đầu trong quá '
                   'trình chuyển đổi. Thành phố lớn cần hành động mạnh mẽ thay vì chờ mọi người tự thay đổi thói quen. '
                   'Nhiều nước đã hướng tới giao thông xanh, nên việc hạn chế xe xăng là xu thế không thể tránh. Vì '
                   'vậy, xe xăng nên bị giới hạn càng sớm càng tốt.',
  'fallacy_hint': 'nguyên nhân đơn nhất',
  'target_flaws': ['coi xe xăng là nguyên nhân chính duy nhất',
                   'xem nhẹ chi phí chuyển đổi',
                   'viện dẫn xu thế như bằng chứng'],
  'expected_rebuttal_points': ['đo tỷ trọng phát thải theo nguồn',
                               'cải thiện giao thông công cộng và hạ tầng sạc',
                               'có lộ trình hỗ trợ nhóm thu nhập thấp']},
 {'id': 'qr_034',
  'topic_id': 'env_consumer_climate',
  'topic': 'Người tiêu dùng có trách nhiệm với biến đổi khí hậu không?',
  'category': 'Môi trường',
  'difficulty': 'Trung cấp',
  'weak_argument': 'Người tiêu dùng có trách nhiệm lớn với biến đổi khí hậu vì mỗi lựa chọn mua sắm đều tác động đến '
                   'môi trường. Nếu mọi người dùng ít nhựa hơn, mua sản phẩm xanh hơn và tiết kiệm điện hơn, biến đổi '
                   'khí hậu chắc chắn sẽ được kiểm soát tốt hơn. Doanh nghiệp chỉ sản xuất những gì người tiêu dùng '
                   'muốn, nên trách nhiệm chính vẫn nằm ở người mua. Việc đổ lỗi cho chính phủ hay tập đoàn chỉ làm cá '
                   'nhân né tránh trách nhiệm của mình. Khi đủ nhiều người thay đổi thói quen, thị trường sẽ tự chuyển '
                   'sang hướng bền vững. Vì vậy, người tiêu dùng là lực lượng quan trọng nhất trong cuộc chiến khí '
                   'hậu.',
  'fallacy_hint': 'chuyển trách nhiệm hệ thống sang cá nhân',
  'target_flaws': ['coi nhu cầu quyết định hoàn toàn sản xuất',
                   'xem nhẹ chính phủ và doanh nghiệp',
                   'gọi người tiêu dùng là lực lượng quan trọng nhất'],
  'expected_rebuttal_points': ['trách nhiệm phải được chia sẻ',
                               'lựa chọn cá nhân bị giới hạn bởi giá và hạ tầng',
                               'chính sách và doanh nghiệp có đòn bẩy phát thải lớn']},
 {'id': 'qr_035',
  'topic_id': 'env_energy_price_saving',
  'topic': 'Có nên tăng giá điện để khuyến khích tiết kiệm năng lượng?',
  'category': 'Môi trường',
  'difficulty': 'Nâng cao',
  'weak_argument': 'Nên tăng giá điện để khuyến khích tiết kiệm năng lượng vì khi điện đắt hơn, người dân sẽ tự động '
                   'dùng ít lại. Nếu mọi gia đình giảm tiêu thụ điện, áp lực lên hệ thống năng lượng và môi trường '
                   'chắc chắn sẽ giảm. Những người phản đối tăng giá thường chỉ nhìn vào chi phí trước mắt mà quên lợi '
                   'ích lâu dài. Người thu nhập thấp cũng sẽ học cách sử dụng điện hợp lý hơn nếu giá điện phản ánh '
                   'đúng giá trị của nó. Nhà nước không thể chỉ kêu gọi tiết kiệm mà không tạo áp lực kinh tế rõ ràng. '
                   'Vì vậy, tăng giá điện là biện pháp hiệu quả để thay đổi hành vi tiêu dùng.',
  'fallacy_hint': 'bỏ qua tác động phân phối',
  'target_flaws': ['giả định tăng giá luôn giảm dùng',
                   'xem nhẹ nhu cầu thiết yếu',
                   'gán động cơ ngắn hạn cho người phản đối'],
  'expected_rebuttal_points': ['dùng biểu giá bậc thang và hỗ trợ hộ nghèo',
                               'đầu tư thiết bị tiết kiệm và thông tin',
                               'đánh giá độ co giãn nhu cầu điện']},
 {'id': 'qr_036',
  'topic_id': 'health_sugary_drinks_school',
  'topic': 'Có nên giới hạn đồ uống có đường trong trường học?',
  'category': 'Sức khỏe',
  'difficulty': 'Cơ bản',
  'weak_argument': 'Nên giới hạn đồ uống có đường trong trường học vì đây là nguyên nhân chính khiến học sinh bị béo '
                   'phì và sâu răng. Nếu căn tin không bán nước ngọt, học sinh chắc chắn sẽ chọn nước lọc hoặc đồ uống '
                   'lành mạnh hơn. Những lựa chọn cá nhân không nên được đặt cao hơn sức khỏe của học sinh. Phụ huynh '
                   'và nhà trường có trách nhiệm kiểm soát môi trường ăn uống thay vì để trẻ tự quyết định. Việc giới '
                   'hạn đồ uống có đường sẽ tạo thói quen tốt ngay từ nhỏ. Vì vậy, trường học nên kiểm soát chặt các '
                   'loại đồ uống này.',
  'fallacy_hint': 'nguyên nhân đơn nhất',
  'target_flaws': ['gọi đồ uống là nguyên nhân chính',
                   'giả định học sinh tự chọn đồ lành mạnh',
                   'bỏ qua nhiều yếu tố sức khỏe'],
  'expected_rebuttal_points': ['béo phì và sâu răng có nhiều nguyên nhân',
                               'bảo đảm lựa chọn thay thế dễ tiếp cận',
                               'kết hợp giới hạn với giáo dục dinh dưỡng']},
 {'id': 'qr_037',
  'topic_id': 'health_mental_health_subject',
  'topic': 'Học sinh có nên được học sức khỏe tinh thần như môn chính khóa?',
  'category': 'Sức khỏe',
  'difficulty': 'Trung cấp',
  'weak_argument': 'Học sinh nên được học sức khỏe tinh thần như môn chính khóa vì hiện nay rất nhiều em gặp áp lực '
                   'học tập và cảm xúc. Nếu có môn học riêng, học sinh chắc chắn sẽ biết cách kiểm soát căng thẳng và '
                   'tránh các vấn đề tâm lý nghiêm trọng. Những môn học hiện tại chỉ tập trung vào kiến thức mà chưa '
                   'quan tâm đủ đến đời sống nội tâm. Việc thêm môn sức khỏe tinh thần sẽ giúp trường học trở nên nhân '
                   'văn hơn. Nếu không đưa vào chính khóa, học sinh sẽ tiếp tục xem nhẹ tâm lý của mình. Vì vậy, sức '
                   'khỏe tinh thần nên được dạy như một môn bắt buộc.',
  'fallacy_hint': 'hứa hẹn quá mức',
  'target_flaws': ['giả định một môn học ngăn được vấn đề nghiêm trọng',
                   'coi bắt buộc là phương án duy nhất',
                   'bỏ qua năng lực chuyên môn hỗ trợ'],
  'expected_rebuttal_points': ['cần giáo viên được đào tạo và hệ thống chuyển tuyến',
                               'có thể tích hợp kỹ năng thay vì thêm môn riêng',
                               'bảo vệ riêng tư và tránh kỳ thị']},
 {'id': 'qr_038',
  'topic_id': 'health_fast_food_ads',
  'topic': 'Có nên cấm quảng cáo đồ ăn nhanh cho trẻ em?',
  'category': 'Sức khỏe',
  'difficulty': 'Trung cấp',
  'weak_argument': 'Nên cấm quảng cáo đồ ăn nhanh cho trẻ em vì trẻ nhỏ rất dễ bị ảnh hưởng bởi hình ảnh hấp dẫn trên '
                   'truyền hình và mạng xã hội. Nếu không còn quảng cáo, trẻ chắc chắn sẽ ít đòi ăn đồ chiên rán và '
                   'nước ngọt hơn. Các công ty đồ ăn nhanh chỉ quan tâm lợi nhuận nên không thể tự kiểm soát trách '
                   'nhiệm của mình. Phụ huynh cũng khó chống lại quảng cáo khi trẻ nhìn thấy chúng quá thường xuyên. '
                   'Những ý kiến cho rằng giáo dục dinh dưỡng là đủ đang đánh giá thấp sức mạnh của truyền thông. Vì '
                   'vậy, cấm quảng cáo đồ ăn nhanh cho trẻ em là cách bảo vệ sức khỏe hiệu quả nhất.',
  'fallacy_hint': 'giải pháp đơn nhất',
  'target_flaws': ['khẳng định cấm quảng cáo chắc chắn đổi hành vi',
                   'quy động cơ doanh nghiệp hoàn toàn vì lợi nhuận',
                   'gọi lệnh cấm là hiệu quả nhất'],
  'expected_rebuttal_points': ['đánh giá mức ảnh hưởng thực tế của quảng cáo',
                               'kết hợp giáo dục và môi trường thực phẩm',
                               'xác định rõ phạm vi và nền tảng áp dụng']},
 {'id': 'qr_039',
  'topic_id': 'health_sleep_vs_extra_classes',
  'topic': 'Ngủ đủ có quan trọng hơn học thêm không?',
  'category': 'Sức khỏe',
  'difficulty': 'Cơ bản',
  'weak_argument': 'Ngủ đủ quan trọng hơn học thêm vì một học sinh thiếu ngủ sẽ không thể tiếp thu kiến thức hiệu quả. '
                   'Nếu học sinh ngủ đủ, các em chắc chắn sẽ tỉnh táo hơn và học tốt hơn mà không cần học thêm quá '
                   'nhiều. Học thêm thường chỉ làm học sinh mệt và tăng áp lực không cần thiết. Những phụ huynh cho '
                   'con học thêm nhiều đang quá chú trọng điểm số mà quên sức khỏe. Chỉ cần cải thiện giấc ngủ, kết '
                   'quả học tập của học sinh sẽ thay đổi rõ rệt. Vì vậy, ngủ đủ nên được ưu tiên hơn mọi hình thức học '
                   'thêm.',
  'fallacy_hint': 'so sánh lưỡng phân',
  'target_flaws': ['coi học thêm thường chỉ gây hại',
                   'hứa hẹn ngủ đủ tự cải thiện kết quả',
                   'bỏ qua nhu cầu từng học sinh'],
  'expected_rebuttal_points': ['giấc ngủ là điều kiện nền tảng nhưng không thay thế mọi hỗ trợ học',
                               'đánh giá chất lượng và lịch học thêm',
                               'cân bằng theo nhu cầu cá nhân']},
 {'id': 'qr_040',
  'topic_id': 'health_school_psych_check',
  'topic': 'Có nên kiểm tra sức khỏe tâm lý định kỳ ở trường?',
  'category': 'Sức khỏe',
  'difficulty': 'Nâng cao',
  'weak_argument': 'Nên kiểm tra sức khỏe tâm lý định kỳ ở trường vì nhiều học sinh có vấn đề tâm lý nhưng không dám '
                   'nói ra. Nếu kiểm tra thường xuyên, nhà trường chắc chắn sẽ phát hiện sớm và ngăn chặn các hậu quả '
                   'nghiêm trọng. Việc này cũng giúp giáo viên hiểu học sinh hơn thay vì chỉ nhìn vào điểm số. Những '
                   'lo ngại về quyền riêng tư không quan trọng bằng sự an toàn tinh thần của học sinh. Khi đã kiểm tra '
                   'sức khỏe thể chất, trường học cũng nên kiểm tra sức khỏe tâm lý theo cách tương tự. Vì vậy, kiểm '
                   'tra tâm lý định kỳ nên trở thành hoạt động bắt buộc.',
  'fallacy_hint': 'đánh đổi quyền riêng tư thiếu cân nhắc',
  'target_flaws': ['giả định sàng lọc luôn phát hiện sớm',
                   'xem nhẹ đồng thuận và bảo mật',
                   'so sánh máy móc với khám thể chất'],
  'expected_rebuttal_points': ['sàng lọc cần tự nguyện hoặc đồng thuận phù hợp',
                               'phải xử lý sai số và có dịch vụ chuyển tuyến',
                               'giới hạn người tiếp cận dữ liệu tâm lý']},
 {'id': 'qr_041',
  'topic_id': 'culture_online_negative_reviews',
  'topic': 'Review tiêu cực trên mạng có nên bị kiểm soát?',
  'category': 'Văn hóa',
  'difficulty': 'Trung cấp',
  'weak_argument': 'Review tiêu cực trên mạng nên bị kiểm soát vì một vài nhận xét xấu có thể làm ảnh hưởng nghiêm '
                   'trọng đến uy tín của cá nhân hoặc doanh nghiệp. Nếu ai cũng được viết đánh giá tiêu cực tùy ý, môi '
                   'trường mạng sẽ trở nên độc hại và thiếu công bằng. Nhiều người dùng review để trút giận hơn là '
                   'phản ánh sự thật khách quan. Vì vậy, nền tảng cần kiểm duyệt mạnh những đánh giá có nội dung tiêu '
                   'cực. Những người thật sự có góp ý vẫn có thể gửi riêng thay vì công khai làm tổn hại người khác. '
                   'Do đó, kiểm soát review tiêu cực là cần thiết để bảo vệ danh tiếng.',
  'fallacy_hint': 'đánh đồng tiêu cực với độc hại',
  'target_flaws': ['coi nhận xét xấu là thiếu công bằng',
                   'suy từ một số lạm dụng sang kiểm duyệt rộng',
                   'đẩy góp ý hợp pháp vào kênh riêng'],
  'expected_rebuttal_points': ['phân biệt review sai sự thật với phê bình chính đáng',
                               'dùng xác minh và cơ chế phản hồi',
                               'bảo vệ quyền thông tin của người tiêu dùng']},
 {'id': 'qr_042',
  'topic_id': 'culture_movies_youth_behavior',
  'topic': 'Phim ảnh có ảnh hưởng mạnh đến hành vi giới trẻ không?',
  'category': 'Văn hóa',
  'difficulty': 'Cơ bản',
  'weak_argument': 'Phim ảnh có ảnh hưởng rất mạnh đến hành vi giới trẻ vì các em thường bắt chước những nhân vật mình '
                   'yêu thích. Nếu phim có nhiều cảnh bạo lực, nổi loạn hoặc lối sống xa hoa, giới trẻ chắc chắn sẽ bị '
                   'tác động theo hướng tiêu cực. Những người nói phim chỉ là giải trí đang xem nhẹ sức mạnh của hình '
                   'ảnh và cảm xúc. Khi một nội dung được xem lặp lại nhiều lần, nó sẽ dần thay đổi cách suy nghĩ của '
                   'người xem. Vì vậy, các nhà làm phim phải chịu trách nhiệm lớn hơn với hành vi của giới trẻ. Do đó, '
                   'cần kiểm soát chặt nội dung phim dành cho người trẻ.',
  'fallacy_hint': 'nhầm tương quan với nhân quả',
  'target_flaws': ['khẳng định phim chắc chắn đổi hành vi',
                   'xem nhẹ các yếu tố gia đình xã hội',
                   'quy trách nhiệm lớn cho nhà làm phim'],
  'expected_rebuttal_points': ['phim chỉ là một trong nhiều yếu tố',
                               'cần bằng chứng về mức độ và nhóm tuổi',
                               'ưu tiên phân loại độ tuổi và giáo dục truyền thông']},
 {'id': 'qr_043',
  'topic_id': 'culture_fandom_pressure',
  'topic': 'Văn hóa thần tượng có gây áp lực cho học sinh không?',
  'category': 'Văn hóa',
  'difficulty': 'Cơ bản',
  'weak_argument': 'Văn hóa thần tượng gây áp lực cho học sinh vì các em thường so sánh bản thân với hình ảnh hoàn hảo '
                   'của idol. Khi thấy thần tượng xinh đẹp, nổi tiếng và thành công từ sớm, học sinh dễ cảm thấy mình '
                   'kém cỏi hơn. Việc mua album, vé xem biểu diễn hay hàng hóa thần tượng cũng khiến các em tiêu tiền '
                   'thiếu kiểm soát. Những người bảo vệ văn hóa thần tượng chỉ nhìn vào niềm vui mà bỏ qua áp lực tâm '
                   'lý phía sau. Nếu không có thần tượng, học sinh chắc chắn sẽ tập trung hơn vào bản thân và học tập. '
                   'Vì vậy, văn hóa thần tượng nên được hạn chế trong môi trường học đường.',
  'fallacy_hint': 'khái quát hóa một chiều',
  'target_flaws': ['chỉ nêu tác hại', 'giả định không có thần tượng sẽ học tốt hơn', 'áp dụng cho mọi học sinh'],
  'expected_rebuttal_points': ['ảnh hưởng khác nhau theo cách tham gia',
                               'văn hóa hâm mộ cũng có lợi ích cộng đồng',
                               'giáo dục tài chính và hình ảnh cơ thể phù hợp hơn cấm đoán']},
 {'id': 'qr_044',
  'topic_id': 'culture_traditional_values_school',
  'topic': 'Trường học có nên dạy nhiều hơn về giá trị văn hóa truyền thống?',
  'category': 'Văn hóa',
  'difficulty': 'Trung cấp',
  'weak_argument': 'Trường học nên tăng mạnh thời lượng dạy giá trị văn hóa truyền thống vì học sinh ngày nay đang dần '
                   'xa rời nguồn cội. Nếu các em học nhiều hơn về lễ nghi, ca dao, phong tục và lịch sử địa phương, '
                   'chắc chắn các em sẽ trở thành người có đạo đức tốt hơn. Những môn học hiện đại như công nghệ hay '
                   'ngoại ngữ có thể học sau, còn văn hóa truyền thống mới là nền tảng quan trọng nhất để hình thành '
                   'nhân cách. Hơn nữa, nhiều người lớn thường nói rằng thế hệ trẻ hiện nay ít quan tâm đến truyền '
                   'thống, nên nhà trường cần ưu tiên nội dung này ngay lập tức. Việc tăng thời lượng học văn hóa '
                   'truyền thống sẽ giúp giải quyết sự xuống cấp về ý thức và lối sống của học sinh. Vì vậy, đây nên '
                   'là một thay đổi bắt buộc trong chương trình giáo dục.',
  'fallacy_hint': 'nguyên nhân giả',
  'target_flaws': ['đồng nhất học truyền thống với đạo đức',
                   'đặt văn hóa đối lập công nghệ ngoại ngữ',
                   'dựa vào nhận xét của người lớn'],
  'expected_rebuttal_points': ['cần xác định giá trị nào và cách dạy nào hiệu quả',
                               'chương trình nên cân bằng truyền thống với kỹ năng hiện đại',
                               'không thể quy xuống cấp lối sống cho thiếu thời lượng môn học']},
 {'id': 'qr_045',
  'topic_id': 'culture_global_content',
  'topic': 'Nội dung giải trí quốc tế có làm giới trẻ xa rời văn hóa địa phương?',
  'category': 'Văn hóa',
  'difficulty': 'Nâng cao',
  'weak_argument': 'Nội dung giải trí quốc tế làm giới trẻ xa rời văn hóa địa phương vì các em tiếp xúc với nhạc, phim '
                   'và xu hướng nước ngoài quá nhiều. Khi giới trẻ yêu thích văn hóa quốc tế, họ chắc chắn sẽ ít quan '
                   'tâm hơn đến phong tục, ngôn ngữ và nghệ thuật truyền thống. Những nền tảng toàn cầu đang khiến văn '
                   'hóa địa phương dần bị lấn át trong đời sống hằng ngày. Việc nói rằng giới trẻ có thể tiếp nhận cả '
                   'hai nền văn hóa là quá lạc quan. Nếu muốn bảo vệ bản sắc, cần hạn chế bớt ảnh hưởng của nội dung '
                   'giải trí quốc tế. Vì vậy, nội dung quốc tế nên được kiểm soát để giữ gìn văn hóa địa phương.',
  'fallacy_hint': 'lưỡng phân văn hóa',
  'target_flaws': ['coi yêu thích quốc tế làm giảm yêu địa phương',
                   'phủ nhận khả năng tiếp nhận cả hai',
                   'đề xuất kiểm soát thiếu tiêu chí'],
  'expected_rebuttal_points': ['bản sắc có thể lai ghép và cùng tồn tại',
                               'đầu tư nội dung địa phương hấp dẫn',
                               'cần bằng chứng trước khi hạn chế quyền tiếp cận']},
 {'id': 'qr_046',
  'topic_id': 'media_influencer_ads',
  'topic': 'Influencer có trách nhiệm với nội dung họ quảng cáo không?',
  'category': 'Truyền thông',
  'difficulty': 'Trung cấp',
  'weak_argument': 'Influencer chắc chắn phải chịu trách nhiệm với mọi sản phẩm họ quảng cáo vì người theo dõi tin '
                   'tưởng vào lời giới thiệu của họ. Nếu một influencer quảng cáo sản phẩm kém chất lượng, họ đã trực '
                   'tiếp góp phần gây hại cho người mua. Việc nói rằng họ chỉ là người truyền thông không đủ để miễn '
                   'trách nhiệm. Khi đã nhận tiền quảng cáo, họ phải bảo đảm sản phẩm là tốt và an toàn. Người nổi '
                   'tiếng trên mạng có ảnh hưởng lớn nên cần bị kiểm soát nghiêm hơn người dùng bình thường. Vì vậy, '
                   'influencer phải chịu trách nhiệm gần như hoàn toàn với nội dung quảng cáo của mình.',
  'fallacy_hint': 'quy trách nhiệm tuyệt đối',
  'target_flaws': ['đòi bảo đảm mọi sản phẩm tốt và an toàn',
                   'xem nhẹ trách nhiệm thương hiệu và nền tảng',
                   'không phân biệt mức độ lỗi'],
  'expected_rebuttal_points': ['influencer phải công khai tài trợ và thẩm tra hợp lý',
                               'trách nhiệm phụ thuộc kiến thức và mức độ sơ suất',
                               'thương hiệu cùng nền tảng phải chịu trách nhiệm']},
 {'id': 'qr_047',
  'topic_id': 'media_short_video_harm',
  'topic': 'Có nên giới hạn nội dung độc hại trên nền tảng video ngắn?',
  'category': 'Truyền thông',
  'difficulty': 'Trung cấp',
  'weak_argument': 'Nên giới hạn nội dung độc hại trên nền tảng video ngắn vì người trẻ rất dễ bị ảnh hưởng bởi những '
                   'gì họ xem hằng ngày. Nếu các video bạo lực, phản cảm hoặc sai lệch bị hạn chế, hành vi của giới '
                   'trẻ chắc chắn sẽ tốt hơn. Nền tảng video ngắn thường ưu tiên nội dung gây sốc để giữ chân người '
                   'xem, nên không thể để họ tự kiểm soát. Những lo ngại về tự do sáng tạo không quan trọng bằng việc '
                   'bảo vệ trẻ em và thanh thiếu niên. Khi nội dung độc hại giảm, môi trường mạng sẽ tự động trở nên '
                   'lành mạnh hơn. Vì vậy, cần giới hạn mạnh các nội dung này.',
  'fallacy_hint': 'khái niệm mơ hồ và hứa hẹn quá mức',
  'target_flaws': ['không định nghĩa nội dung độc hại',
                   'xem nhẹ tự do sáng tạo',
                   'giả định giảm nội dung sẽ tự tạo môi trường lành mạnh'],
  'expected_rebuttal_points': ['đặt tiêu chí rõ và nhất quán',
                               'có minh bạch cùng cơ chế kháng nghị',
                               'kết hợp kiểm duyệt với kỹ năng số và công cụ phụ huynh']},
 {'id': 'qr_048',
  'topic_id': 'media_fake_news_label',
  'topic': 'Nền tảng mạng xã hội có nên gắn nhãn cảnh báo tin giả?',
  'category': 'Truyền thông',
  'difficulty': 'Nâng cao',
  'weak_argument': 'Nền tảng mạng xã hội nên gắn nhãn cảnh báo tin giả vì người dùng thường không đủ thời gian để tự '
                   'kiểm chứng mọi thông tin. Nếu một bài đăng được gắn nhãn, người đọc chắc chắn sẽ cẩn trọng hơn và '
                   'ít chia sẻ sai lệch hơn. Các nền tảng có công nghệ kiểm duyệt nên họ hoàn toàn có thể xác định nội '
                   'dung nào đáng ngờ. Những lỗi gắn nhãn sai không nghiêm trọng bằng tác hại của việc để tin giả lan '
                   'truyền tự do. Người dùng cần được hướng dẫn bởi hệ thống thay vì tự đánh giá mọi thứ. Vì vậy, gắn '
                   'nhãn cảnh báo là giải pháp hiệu quả để chống tin giả.',
  'fallacy_hint': 'tin tưởng quá mức vào kiểm duyệt',
  'target_flaws': ['giả định nền tảng xác định đúng nội dung',
                   'xem nhẹ tác hại gắn nhãn sai',
                   'coi người dùng không thể tự đánh giá'],
  'expected_rebuttal_points': ['nhãn nên thể hiện mức độ bất định và nguồn kiểm chứng',
                               'cần quy trình sửa sai và kháng nghị',
                               'kết hợp nhãn với giáo dục kiểm chứng']},
 {'id': 'qr_049',
  'topic_id': 'media_children_fast_news',
  'topic': 'Học sinh có nên được dạy cách kiểm chứng thông tin trên mạng?',
  'category': 'Truyền thông',
  'difficulty': 'Cơ bản',
  'weak_argument': 'Học sinh nên được dạy cách kiểm chứng thông tin trên mạng vì các em thường tin vào những gì xuất '
                   'hiện đầu tiên trên Internet. Nếu học sinh biết kiểm tra nguồn, so sánh thông tin và nhận diện tin '
                   'giả, các em chắc chắn sẽ không bị lừa nữa. Kỹ năng này quan trọng hơn nhiều nội dung học thuật vì '
                   'mạng xã hội ảnh hưởng trực tiếp đến đời sống hằng ngày. Nhà trường nên bắt buộc dạy kiểm chứng '
                   'thông tin để bảo vệ học sinh khỏi tin sai lệch. Những kỹ năng này nếu không học ở trường thì học '
                   'sinh khó có thể tự hình thành. Vì vậy, dạy kiểm chứng thông tin sẽ giải quyết được phần lớn vấn đề '
                   'tin giả trong giới trẻ.',
  'fallacy_hint': 'hứa hẹn quá mức',
  'target_flaws': ['khẳng định học xong sẽ không bị lừa',
                   'đặt kỹ năng này cao hơn nhiều nội dung khác',
                   'coi nhà trường là nơi duy nhất hình thành kỹ năng'],
  'expected_rebuttal_points': ['kỹ năng cần luyện thường xuyên với tình huống thật',
                               'gia đình và nền tảng cũng có trách nhiệm',
                               'đánh giá hiệu quả thay vì hứa giải quyết phần lớn tin giả']},
 {'id': 'qr_050',
  'topic_id': 'media_comments_real_name',
  'topic': 'Bình luận trên mạng có nên bắt buộc dùng tên thật?',
  'category': 'Truyền thông',
  'difficulty': 'Nâng cao',
  'weak_argument': 'Bình luận trên mạng nên bắt buộc dùng tên thật vì ẩn danh khiến nhiều người dễ xúc phạm và lan '
                   'truyền thông tin sai. Nếu mọi người phải dùng danh tính thật, họ chắc chắn sẽ cư xử văn minh và có '
                   'trách nhiệm hơn. Những người không làm gì sai sẽ không có lý do để sợ việc công khai tên của mình. '
                   'Việc bảo vệ quyền ẩn danh chỉ tạo cơ hội cho các hành vi độc hại tiếp tục tồn tại. Nền tảng mạng '
                   'xã hội sẽ dễ quản lý hơn nếu mỗi bình luận gắn với một con người thật. Vì vậy, bắt buộc dùng tên '
                   'thật là cách hiệu quả để làm sạch môi trường mạng.',
  'fallacy_hint': 'lập luận không có gì phải giấu',
  'target_flaws': ['đồng nhất ẩn danh với hành vi độc hại',
                   'bỏ qua người cần bảo vệ danh tính',
                   'giả định tên thật bảo đảm văn minh'],
  'expected_rebuttal_points': ['ẩn danh bảo vệ nạn nhân và người bất đồng chính kiến',
                               'có thể xác minh kín mà vẫn dùng bút danh',
                               'kiểm duyệt hành vi hiệu quả hơn công khai danh tính']}]
