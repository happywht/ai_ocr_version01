# 增加PDF格式支持的实现计划（优化版）

## 1. 问题分析
当前项目只支持图片格式的发票识别，需要扩展为支持PDF格式。核心问题包括：
- `recognize_image`方法只处理图片文件
- GUI文件选择对话框只显示图片格式
- 缺少处理PDF的依赖库

## 2. 解决方案
### 2.1 选择更友好的PDF处理方案
考虑到用户体验，我们将使用`pypdfium2`库来处理PDF，它是一个纯Python库，不需要额外安装系统依赖，相比`pdf2image`更加友好。

### 2.2 修改核心识别逻辑
- 修改`invoice_ocr_tool.py`中的`recognize_image`方法，增加PDF处理分支
- 对于PDF文件，将其转换为图片后再进行OCR识别
- 支持多页PDF的处理

### 2.3 更新GUI界面
- 修改`invoice_gui_v2.py`中的文件选择对话框，添加PDF格式选项
- 更新图片预览功能，支持PDF预览

### 2.4 更新依赖检查和安装脚本
- 更新`start_gui.py`中的依赖检查，添加pypdfium2
- 更新`requirements.txt`，添加pypdfium2依赖

## 3. 实现步骤

### 步骤1：更新依赖文件
- 修改`requirements.txt`，添加`pypdfium2>=4.30.0`
- 更新`start_gui.py`中的`check_dependencies`函数，添加pypdfium2检查

### 步骤2：修改核心识别逻辑
1. 在`invoice_ocr_tool.py`中添加PDF处理导入
2. 修改`recognize_image`方法，增加PDF处理分支：
   ```python
   if image_path.lower().endswith('.pdf'):
       # PDF处理逻辑
       import pypdfium2 as pdfium
       # 打开PDF文件
       pdf = pdfium.PdfDocument(image_path)
       # 处理每一页
       results = []
       for page_num in range(len(pdf)):
           # 获取页面
           page = pdf[page_num]
           # 渲染页面为图片
           pil_image = page.render(
               scale=2.0,  # 提高分辨率以获得更好的OCR效果
               color_mode=pdfium.BitmapColorMode.RGB,
           ).to_pil()
           # 将PIL Image转换为二进制数据
           import io
           image_stream = io.BytesIO()
           pil_image.save(image_stream, format='PNG')
           image_data = image_stream.getvalue()
           # 调用OCR识别
           results.append(ocr_result)
       # 合并结果或返回多页结果
   else:
       # 原有图片处理逻辑
   ```
3. 更新`process_invoice`方法，支持多页PDF的处理

### 步骤3：更新GUI界面
1. 修改`invoice_gui_v2.py`中的`select_image`方法，在文件类型中添加PDF格式：
   ```python
   file_types = [
       ('支持的文件', '*.jpg *.jpeg *.png *.bmp *.tiff *.pdf'),
       ('PDF文件', '*.pdf'),
       # 其他文件类型
   ]
   ```
2. 更新`display_image_preview`方法，支持PDF预览：
   ```python
   if image_path.lower().endswith('.pdf'):
       # 提取PDF第一页作为预览
       import pypdfium2 as pdfium
       pdf = pdfium.PdfDocument(image_path)
       page = pdf[0]
       # 渲染页面为图片
       pil_image = page.render(
           scale=1.0,
           color_mode=pdfium.BitmapColorMode.RGB,
       ).to_pil()
       # 后续处理与图片相同
   else:
       # 原有图片预览逻辑
   ```

### 步骤4：测试和优化
- 测试单页PDF的识别
- 测试多页PDF的识别
- 优化PDF转换和识别性能
- 处理异常情况，如密码保护的PDF

## 4. 预期效果
- 用户可以选择PDF格式的发票文件进行识别
- 系统会自动将PDF转换为图片并进行OCR识别
- 支持多页PDF，返回每一页的识别结果
- GUI界面可以预览PDF文件
- 无需手动安装额外的系统依赖，提升用户体验

## 5. 依赖说明
- `pypdfium2>=4.30.0`：纯Python库，用于将PDF转换为图片，无需额外系统依赖

## 6. 注意事项
- 对于大文件或多页PDF，可能需要较长的处理时间
- 需要处理各种异常情况，如损坏的PDF文件
- 确保pypdfium2库与Python版本兼容