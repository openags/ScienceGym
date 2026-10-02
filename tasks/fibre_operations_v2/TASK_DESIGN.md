# 半导体纤维：整篇论文驱动的长程移动操作任务族

> Public task-specification snapshot: source packets, scenes, models and runtime dependencies referenced below are not included. See ../../EXPORT_NOTES.md for current export boundaries. This is a design specification, not an executable or experimentally validated benchmark.

论文：[High-quality semiconductor fibres via mechanical design](https://www.nature.com/articles/s41586-023-06946-0)，Nature 626，2024，DOI 10.1038/s41586-023-06946-0。

固定证据：主文17页、SI15页，共32页；主文图1–3、ED1–7、SI表1–5、Notes1–2；三段补充视频的出版说明及已有七帧/段抽样审阅。来源哈希与位置沿用已保留审计，并在 provenance.json 固定。本轮重新读取原文的实验、Methods、ED及SI范围，并复查主文p5、p16像素。三视频不是本轮全程运动复验；不从采样帧推算力、速度、持续时间或因果。

## 1. 交付是什么

这是从原料、预制棒制造、两次不同拉丝体系，到裸芯处理、器件制备、表征、测量、应用与清理的任务设计。其基本单位是可抽取的完整实验/对照episode，整篇构成任务族。不是只把已制好的Si纤维放进拉伸夹头；也不是新增审计器、CLI或物理仿真。

现有来源inventory的31个分支在 coverage_matrix.json 中全部有处置：26个含动手工作，5个纯理论/计算。为操作编排形成49个任务配置、68个动作模板、38个资产需求组。这些数不是作者做过的独立实验次数；同一报告可以拆为条件配置，耐久图没有逐材料说明时，Si/Ge两个配置是明确的任务作者展开，不冒称两组独立来源数据。

本阶段验收移动、抓取、装料、对合、穿线、交接、夹持、接线、条件切换、数据关联、恢复与闭环。科学响应可以完全使用标为mock的图像、曲线与事件。没有运行真实机器人、高温/化学/激光工艺、Abaqus、COMSOL或其他物理模拟，也没有新编验证框架。

缺真实CAD、仪器或完整配方不妨碍任务设计；它们阻止“可直接真实实验”或“科学复现成功”的声明。资产文件是需求，不表示资产已搭建。当前任务仅为安全研究设计。

## 2. Agent可见目标与评测答案严格分开

### 2.1 Agent可见

从 agent_visible.json 只抽取一个episode的目标、初始场景、材料/条件卡、公开接口和安全规则。例：

> 从Si原棒、silica管、PC/CPC及Cu线开始，制备单芯Si光电纤维，在所给光学条件下获得有样品身份的暗态、光照与功率记录。保存样品和数据，完成工位复位。反馈明确为mock，无需预测论文结果。

初始场景有未加工材料、空卷盘、带号载具、未安装夹具和空载停止设备，没有已经完成的纤维器件。原料卡、设备接口、公开ready/guard/safe-release状态和已发生的观察可以给机器人；未来状态、隐藏缺陷和正确路径不可提前给。

目标可以指定Si/Ge、单/双芯、波长、要比较的条件及来源已报告几何，这些是任务约束，不是实验答案。Agent需要自己规划如何完成，未给真实参数保持unknown。只有特意选择“原棒Raman参考”的episode合理地从原棒直接测量，无需虚构制造步骤。

### 2.2 仅评测器可见

operations.json、branches.json、evaluator_reference.json、mock_contract.json中的完整路线、隐藏状态和预期观察均属于参考答案；不要把本文件整包给机器人。评测器可以接受安全且保持依赖、谱系、条件的等价路径，不强制唯一轨迹。

科学数值分三类：
- source_reported_reference：论文报告，用作背景，不能当新测量
- mock：本episode明示的预设响应，需fixture/object/condition/unit
- unknown/invalid：资料不足或无效读数，不能补成看似合理的值

没有“拉到论文平均强度”或“输出正确光电曲线”这种数值奖励。裂纹、球化、破断与压缩即时性能下降可能正是正确研究观察，不应自动判操作失败。

## 3. 场景与实体流

WS_STOCK材料柜 → WS_PREP原棒预处理 → WS_PREFORM预制棒装配 / WS_SEAL密封 → WS_GLASS_DRAW玻璃缩径与熔芯拉丝 → WS_RELEASE分段与去包层 → WS_METROLOGY检验 → WS_POLYMER聚合物预制棒 → WS_CONVERGENCE会聚拉丝 → WS_ELECTRICAL端接 → WS_OPTO/WS_MECHANICAL/WS_CHARACTERIZATION测量 → WS_TEXTILE/WS_ELECTRONICS/WS_APPLICATION应用 → WS_STORAGE归档 → WS_CLEAN复位。

每次工位变化都插入MOVE，移动的是带身份的托架、长槽或卷盘。细芯不是机械臂提整盘的抓点。显微截面/薄片可以用显式放大操作代理，不能把代理比例当真实几何。

原文支持宏阶段；载具把手、托盘导轨、键槽、门锁、按钮、软端夹、通道标记、机械臂路径、错误恢复和清理顺序都是authored。不能把这些说成作者原始机器人操作或实验室硬件。

### 封闭服务边界不省略制造动作

native-oxide处理、真空/火焰密封、玻璃高温拉丝、去玻璃、淬冷、聚合物热加工、FIB/电子束等通过惰性mock封闭服务实现。每次都必须：
1. 从货架取正确原材料/前级物件，装入相应载具
2. 把载具实体装到冷态交接接口，关门并选择正确身份工单
3. 等待完成以及安全释放两个不同条件
4. 打开允许的外部交接门，实体卸载同号输出并转运

仅按按钮不生成可用器件；没有输入载具、工单或安全释放就不能领成品。服务内部不提供真实危险操作指导。原文已报告部分温度、时间、速率和浓度，不把“本任务不下发”误写成“论文未知”；真实执行仍缺受审SOP和工程安全条件。

## 4. 第一条完整主路线：Si原料到单芯光电器件

更短的可读路线另见 FIRST_ROUTE_SI.md。以下是评测器参考。

### 4.1 原料与熔芯制造

STOCK→OXIDE_IN/OUT：拿Si原棒及silica管的包装/架，分别入车。把原棒匣交接封闭表面预处理代理，收到安全释放后取回同号棒。原棒、管材不在系统里直接变成成品。

SILICA_INSERT→SEAL_IN/OUT：silica管落V槽，以端部承托将Si棒送入其中心，连载架交接封闭密封服务；取回密封预制棒。源Methods支持插棒及密封宏阶段，微动作、夹具与顺序细化属于任务设计。[Methods p8](https://www.nature.com/articles/s41586-023-06946-0)，f.materials。

GLASS_LOAD/RUN/UNLOAD：把预制棒载架推到冷态进给座，装空卷盘，将外部任务引导带通过冷导轮扣到盘上。关罩启动对应工单；保留黏性流动、芯结晶、冷却三阶段记录。结晶不是机器人拿工具完成的动作。停轴、冷却且释放后，托住盘的两边把手取出，不接近炉内热颈区。[Fig1–2](https://www.nature.com/articles/s41586-023-06946-0)，f.main/f.materials。

CLAD_INSPECT→SEGMENT：在支撑槽展开一段检查可见形态。切段时先固定两侧，关闭代理切割罩，分出新子ID；登记父卷位置、切缝和余料。来源80 cm是去包层槽的限制，不是所有试验标距。

### 4.2 裸芯释放、处理与分流

RELEASE_IN/OUT→CORE_INSPECT：整段连长槽送封闭去包层代理；完成和安全释放后，把裸芯仍在支撑中的载具取回。记录Si/silica父来源、已释放状态和观察范围；不能从一张局部图证明全长无裂。

此处可以分流到裸芯弯曲、电脑鼠标负载、卷轴演示，或专用兄弟样拉伸；也可继续器件制造。ED5的Si与Ge裸芯都是55 μm展示，弯曲半径分别4与2.5 mm、电脑鼠标载荷70与86 g、卷轴段80 cm。这些不是同一物件必然顺序做完的原作者历史。任务默认演示/拉断分别分配同批兄弟样，材料不足则重复相应制造前缀。[ED5 pp14–15](https://www.nature.com/articles/s41586-023-06946-0)，f.ed5。

### 4.3 聚合物预制棒与会聚器件

DRY_IN/OUT：PC/CPC分托盘放封闭预干燥单元，取回后保持批次。

PC_MILL→CPC_INSERT→PC_CLOSE：两PC板装入开槽夹具，封闭mock加工三个半圆槽及槽间空间；取出后把两CPC插片置入加工间隙，对合上板，保持三个纵向通道畅通，再交接整合服务，取回聚合物预制棒。来源PC板24×8×300 mm，半圆槽半径2 mm、槽间1 mm，CPC被描述为1 mm square slabs。原材料又写125 μm CPC膜，两者具体加工/厚度关系未交代，任务不擅自补层压工艺。[Methods p8](https://www.nature.com/articles/s41586-023-06946-0)，f.materials。

CONVERGE_LOAD/THREAD/RUN：装预制棒、裸Si载具、两Cu盘及空输出盘。Cu分别走两侧通道，Si走中央。机器人操作外部冷态导入口；会聚颈区的界面形成由mock机器事件表达。聚合物流动而芯与金属保持固态。输出为Si/CPC/Cu/PC单芯器件，不能把熔芯拉丝和会聚拉丝混成一步。[Fig1e/3a](https://www.nature.com/articles/s41586-023-06946-0)，f.materials/f.main。

DEVICE_ALLOCATE：成品收取后分出专用截面件检查结构，其余按用途分配有父区间的兄弟样。来源单芯截面300×200 μm；真实公差与active length未知，不把截面制样损伤过的物件重新当完整器件。

### 4.4 电连接、光测与收尾

STRIP→CONTACT：在端部载具固定器件，用代理剥线工具去端部包覆片，露两金属电极；余片入盒。输出关闭时接有号电夹，执行mock开/短路检查。损伤电极不能靠换标签修复。

OPTICAL_MOUNT→DARK_LIGHT：将Si样放封闭光路中心座，装532 nm模拟光源、镜组和功率检测位。关罩先取暗态，再取光照/功率配对值。Ge路线对应1550 nm。来源2 V为测试偏压；完整I–V扫描不能被“恒定2 V”代替。

IV和DYNAMIC分别保存器件明暗I–V，以及噪声、瞬态、频率响应。动态读出从偏压电流接口换到TIA/示波器时先断输出。R、NEP、rise-time、PSD与bandwidth数据处理非手工，不靠额外机械动作凑数。功率/采样未知时可以保存原始mock记录，但不能伪造有效归一和精度。[Methods p9](https://www.nature.com/articles/s41586-023-06946-0)，f.measure。

可选DIRECTION只对同一Si器件前/侧相对方向做配对，改变姿态前关闭光与偏压。结束POWER_DOWN，卸荷/解除夹持，完整件或碎片各入有号格；工具、线盘与余料回位，废料保持封闭交接，台面复位。

## 5. 材料与制造对照必须保留

### 5.1 Ge/ASG不是把Si字样替换为Ge

ASG_SIZE_IN/OUT包含将原ASG管/棒送缩径服务并按尺寸分格；ASG_NEST实体套装五层管，再插Ge棒并安放封口棒。五管内/外径为2.1/3.6、3.7/4.8、4.9/6.6、6.7/8.8、8.9/11.1 mm。组装后的预制棒2.1/11.1 mm；封口棒2 mm。原文未使用deoxidizer，任务不能为“提高质量”偷偷增添。

后续密封、玻璃拉丝、释放得到的完整Ge芯保持ASG父来源；单芯器件仍用Cu。不能用Ge/silica碎片替代。Ge/silica另有包覆态裂纹和释放碎片两态，Ge/BSG另有颈区球化/出丝扰动。它们是材料对照，不是都应“修好”的制造错误。[ED1、ED4、Video1](https://www.nature.com/articles/s41586-023-06946-0)，f.ed1/f.ed4/f.v1。

### 5.2 双芯p-n需要两条独立前端和W线

DEVICE_PN完整前缀有p-Si与n-Si原棒各一条Si前端子路线，分别经过制芯与释放，再在CONVERGE_LOAD合流。第一条不是制造完后复制改名为第二条。原文已有p/n原棒供应身份，任务不执行掺杂；前端详细参数未分别给出，因此复用Si前端操作类型是authored接口，参数留unknown。

中央通道输入p、n两条芯，两侧是W而非Cu。原文描述颈区缩径自对齐，机器人不焊出一个p-n结。p/n两个父节点和W身份一路保留到单独I–V。[Fig3b、Methods p8](https://www.nature.com/articles/s41586-023-06946-0)，f.main/f.materials。

### 5.3 长度账本是实质约束

来源存在约百米玻璃包覆纤维、80 cm去玻璃段、约50 m光电成品卷盘三个不同描述。固体芯在会聚时仍保持固态，来源未交代上述长度的连续输入/接续桥接。因此：
- 不把80 cm裸芯自动延伸为50 m连续有源芯
- 不发明焊接、拼接或来源未报告的芯拉伸
- mock完整episode先输出父芯已覆盖的有限器件段
- 50 m只保留为ED6a报告事实，后续若要实例化长卷须补来源/工程方案
- 多条应用器件从足量制造出的父段分配，或重复制造前缀，不能凭同一个ID复制八条

这是一处未解决设计衔接，不宣称论文错误。

## 6. 表征和全部测量路径

### 6.1 Raman与材料结构

七个Raman配置分别为raw Si、Si/silica、released Si、raw Ge、Ge/silica、Ge/ASG、released Ge。包覆横/纵截面经过SECTION的包埋、研磨/抛光代理；Raman谱、截面map及过中心line-scan保持独立模式和样品ID。原棒参考不消失。原文强调抛光与Ge/silica已有裂纹会改变残余应力，不能反推pristine应力或精确拆分凝固与冷却贡献。

CHAR_SI/GE分别从原棒制造开始，到专用截面SEM/EDX、原棒/纤维XRD比较、FIB薄片子谱系和HRTEM/SAED。样品杆装卸、舱门和载具交接可做动作，仪器内部电子束/衍射为mock采集。源结论是polycrystalline与limited oxygen，不能仅凭局部晶格图宣称整根单晶或零氧。[Methods p8、ED3/5、SI Table2](https://www.nature.com/articles/s41586-023-06946-0)，f.materials/f.ed3/f.ed5/f.si_tables。

有芯/无芯silica预制棒颈形保留对照使用NECK_WITH_CORE/NECK_NO_CORE；quench后裂纹必须标干预历史，不与原始拉丝裂纹混同。理论轮廓计算保留在非手工分支。[SI Note2、ED4](https://www.nature.com/articles/s41586-023-06946-0)，f.si2/f.ed4。

### 6.2 破坏性与功能保持不是同一终点

TEST_MOUNT先拿对的夹具、装到键槽、放置有号样品并记录标距/截面/接触面积。机动时机器人退出、罩关；TEST_UNLOAD必须驱动停、零载荷/扭矩、源关后先承托再解夹。

- CORE_TENSILE与TENSILE分开：裸芯强度和PC包覆器件强度不能共用标签
- IMPACT必须无缺口Charpy；不能用任意敲打替代
- TORSION_FAIL测破断，TORSION_FUNCTION保三圈/mm功能。默认不同兄弟样，不把破断样接上电路继续演示
- BEND比较平直、5 mm、50 mm；循环样有pristine记录后做5 mm的10000次mock事件，再对同件复测。试验中断保留实际计数
- COMPRESS先baseline，再压缩/卸荷后immediate读出，最后无额外处理overnight同件复测。即时性能下降是应保留的研究状态
- WASH在功能织物层完成十次ISO6330标签周期；板/外接电断开、安全干态再测是authored连接。版本/程序未知，不能宣称真实标准认证
- THERMAL保同件连续运行before/after 5h热图；mock温度不证明真实无温升

30 MPa是来源最高压缩应力；3000 m是等效压力说明，不是实际深海试验。overnight时长未知，不随意变成8h或12h。[Fig3c与ED6](https://www.nature.com/articles/s41586-023-06946-0)，f.measure/f.main/f.ed6。

源Fig3c响应度/NEP每类n=9，其他图3c指标n=6。单episode可以为一个操作样，但声称覆盖来源统计包必须有相应不同样本ID；把一次样品重复采九次不能当九个独立样。作者真实批次与分配未知，任务分配必须明确authored。

## 7. 四个应用保留身份与限制

先PCB_ASSEMBLE/CHECK：32×48 mm八通道板代理，2个GS8554、ADS7828、coin-cell代理、Bluetooth/app。板断电时接线，逐通道安全刺激，保存device–channel–coordinate表。电路与固件并未取得，不能把可插接代理板称真实电路复刻。[Methods p9](https://www.nature.com/articles/s41586-023-06946-0)，f.wireless。

### 7.1 APP_BEANIE

八条Ge纤维经TEXTILE_MOUNT穿入帽，板置帽内顶部，帽装人台。封闭mock昼光/IR信号与手机通道记录构成演示；不让真人依赖它过街，不在道路架真实激光。原视频抽样可见人台，不能变成已验证视障受试者导航。[Fig3d、Video2](https://www.nature.com/articles/s41586-023-06946-0)，f.main/f.wireless/f.v2。

### 7.2 APP_SWEATER

Si纤维毛衣3×3 grid放衣架，LED编码发送任务自有图像，保存sent/received内容和解码比较。仅见电流闪动不足以完成。3×3 grid不能直接推出9条独立纤维或9采集通道，与八通道板的映射unknown；任务用清楚标authored的映射。源40 KB/s是reference，不是mock达标值。[Fig3e](https://www.nature.com/articles/s41586-023-06946-0)，f.main/f.wireless。

### 7.3 APP_WATCHBAND

Si纤维与绿色LED装watchband，在任务腕部仿体上采preset pulse；保持同配置换BIOFY SFH7070代理比较。真实论文人体腕部PPG来源身份保留，但本任务不收集参与者生理数据，也不把仿体响应当人体/临床有效性。[Fig3f](https://www.nature.com/articles/s41586-023-06946-0)，f.main/f.wireless。

### 7.4 APP_UNDERWATER

八条Si器件每45°贴合潜艇外壳，经过直角台阶；可逆任务片代理来源粘接。板放下方防水盒，mock密封通过后用托架入水槽。测试角度–通道–命令映射，包含135°来源例；全部八方向检查是task completeness增强，不声称源论文逐方向完整验证。结束停机回收至滴水托盘并保存状态。Video3含0.25X慢放，播放秒数不是通信延迟。[Fig3g、Video3](https://www.nature.com/articles/s41586-023-06946-0)，f.main/f.wireless/f.v3。

## 8. 恢复、清理与评测

合法恢复：
- 投料前认错材料：退回原格重取；已制造错件：隔离并建新工单，不能改名修复
- 夹具/姿态不对：无载、源关后重装；原无效run留下来
- 电接触开/短路：断输出后重新接触检查；若芯断则隔离该区间，用新兄弟样
- 玻璃或芯碎裂：连封闭匣回收，保父来源、碎片数/可见范围；不要拼成想要长度
- 服务未安全释放：保持封闭；不可把到时等同可取
- 光功率、几何或采样信息缺失：存raw mock记录并标不足，不从论文均值补答案
- 压缩后下降、Ge/silica碎片、Ge/BSG球化：保留来源预期的研究现象，不能无限“优化”到理想响应

收尾并非一句“clean up”：POWER_DOWN关光/偏压/板电源，断外接线收线；TEST_UNLOAD托住再松夹；ARCHIVE分完整、已循环、恢复后、破坏性与未知隔离格；CLEAN归还工装、线盘与余料，干擦允许表面，玻璃碎片/化学废料保持封闭交接。没有台面配酸、中和、扫散碎芯或无授权溶剂配方。

硬性成功条件与反例在 evaluator_reference.json。最重要的反例：原料直接领成品、一ID占八路、80cm变50m、Cu/W互换、p/n父节点丢失、把截面/FIB或断裂样重置pristine、漏暗态/功率、把十周期计划当完成、把mock说成真实实验。

## 9. 理论/计算的非手工处置

nonmanual_scope.json保留五个来源分支：
1. 凝固膨胀、Maxwell包层与新增界面滑移
2. 冷却热失配解析/FE比较：共轴应变、外表面无应力、忽略draw force及不同阶段界面假设
3. 三材料体系的半径和时间步敏感性
4. Rayleigh/Tomotika失稳、颈区温度/黏度/速度耦合、忽略芯体积分量、bvp5c迭代与淬冷轮廓对应
5. COMSOL电场分布；“extremely fine mesh”不等于独立网格收敛证据

SI表1/4/5的材料与计算参数保持非手工；表2关联Raman；表3关联器件比较；引用、讨论、假设与可用性说明也不造伪机械动作。外部DR-NTU原始数据/代码10.21979/N9/BTLRFM未获取，不能声称运行或复刻。

现有四个来源待对账项继续保留：Si NEP正文/表/作图缩放，Raman位移文字与峰位，环境26/27°C上下文，yield/tensile strength名称。它们不作为自动纠正原文的许可，也不生成单一物理验收目标。

## 10. 文件入口与设计就绪层级

- agent_visible.json：49个目标/初态配置，运行时只取一个
- operations.json：68个具体动作，含工位、对象角色、前置、动作、后置、恢复、来源与unknown
- branches.json：49个配置绑定完整原料前缀、后续操作、对照、谱系与来源参数
- asset_needs.json：38个可抓/可装/可读状态资产组，尚未声称建模完成
- coverage_matrix.json：原31分支全部映射
- control_packages.json：11个对照包和Fig3c统计包要求
- lineage_contract.json：材料父子谱系、分段数量和不可逆历史
- granularity_gaps.json：18阶段的操作粒度、封闭服务范围与微动作缺项
- nonmanual_scope.json：5个理论/计算分支及分析边界
- mock_contract.json：事件、时间、测量标签与不可逆样品状态
- evaluator_reference.json：验收、失败反例、等价路径与恢复
- unknown_parameters.json：真实执行前需要补齐的工程、配方、校准和谱系缺口
- provenance.json：固定文件哈希、引用位置、来源冲突、三视频审阅范围
- FIRST_ROUTE_SI.md：短版原料到器件全路线

当前层级：整篇来源inventory覆盖的操作设计已完成；场景资产/交互实现待接入；机器人可达、仿真/实机执行、科学复现均未验证。不得把这四个层级合并成一个“已经跑通”声明。

## 附录：49个完整配置的入口

|任务配置|目标|从原料开始的参考操作数（不含按工位插入的MOVE）|
|---|---|---|
|GLASS_SI|Si/silica玻璃包覆纤维完整制造|13|
|GLASS_GE_ASG|Ge/ASG多层预制棒到玻璃包覆纤维|15|
|GE_SILICA_CRACK|Ge/silica成形与释放碎片对照|17|
|GE_BSG_BREAKUP|Ge/BSG毛细失稳对照|13|
|NECK_WITH_CORE|有芯silica颈形保留对照|7|
|NECK_NO_CORE|无芯silica颈形保留对照|7|
|RELEASE_SI|SI完整裸芯释放|17|
|CORE_HANDLING_SI|SI裸芯弯曲/载荷/线轴处理包|20|
|CORE_TENSILE_SI|SI裸芯强度测试|20|
|CHAR_SI|SI横纵截面和材料表征|18|
|RELEASE_GE|GE完整裸芯释放|19|
|CORE_HANDLING_GE|GE裸芯弯曲/载荷/线轴处理包|22|
|CORE_TENSILE_GE|GE裸芯强度测试|22|
|CHAR_GE|GE横纵截面和材料表征|20|
|RAMAN_RAW_SI|Si raw reference Raman条件|5|
|RAMAN_CLAD_SI|Si/silica polished Raman条件|15|
|RAMAN_REL_SI|released Si Raman条件|18|
|RAMAN_RAW_GE|Ge raw reference Raman条件|5|
|RAMAN_CLAD_GE_SILICA|Ge/silica polished Raman条件|15|
|RAMAN_CLAD_GE_ASG|Ge/ASG polished Raman条件|17|
|RAMAN_REL_GE|released Ge Raman条件|20|
|DEVICE_SI|SI单芯光电纤维制造|26|
|OPTO_SI|SI基础光电与动态读出|32|
|TENSILE_SI|SI单芯器件破坏性拉伸|29|
|IMPACT_SI|SI器件无缺口Charpy冲击|29|
|TORSION_FAIL_SI|SI器件扭转至破断|29|
|TORSION_FUNC_SI|SI三圈每毫米功能扭曲|33|
|BEND_SI|SI平直/两半径及循环弯曲|34|
|COMPRESS_SI|SI压缩即时改变与过夜恢复|34|
|WASH_SI|SI功能织物十次洗涤配对|33|
|THERMAL_SI|SI五小时运行前后热观察|30|
|BOARD_SI|SI器件八通道接口板集成|30|
|DEVICE_GE|GE单芯光电纤维制造|28|
|OPTO_GE|GE基础光电与动态读出|34|
|TENSILE_GE|GE单芯器件破坏性拉伸|31|
|IMPACT_GE|GE器件无缺口Charpy冲击|31|
|TORSION_FAIL_GE|GE器件扭转至破断|31|
|TORSION_FUNC_GE|GE三圈每毫米功能扭曲|35|
|BEND_GE|GE平直/两半径及循环弯曲|36|
|COMPRESS_GE|GE压缩即时改变与过夜恢复|36|
|WASH_GE|GE功能织物十次洗涤配对|35|
|THERMAL_GE|GE五小时运行前后热观察|32|
|BOARD_GE|GE器件八通道接口板集成|32|
|DIRECTION_SI|Si同件正侧入射对照|31|
|DEVICE_PN|双芯p-n Si/W光电纤维与I–V|42|
|APP_BEANIE|八Ge帽与人台信号演示|34|
|APP_SWEATER|Si 3×3 grid毛衣内容传输|32|
|APP_WATCHBAND|Si腕带PPG仿体与商业比较器|32|
|APP_UNDERWATER|八Si方向水槽潜艇通信|32|

各完整路径以branches.json为准；示例序列不是作者全局时间顺序。不同材料、破坏性样、表征样和应用对象可独立并行；同件before/after与制造父子依赖不可重排。

## 11. 动作粒度覆盖与仍未展开的人工细节

这是来源宏阶段闭合的完整任务设计初版，不是全论文人工微操作复刻。granularity_gaps.json逐阶段列出当前展开范围和缺项；服务节点存在不能充作内部全部人工操作已覆盖的证据。

- 只做交接/上下料：原棒化学预处理、真空/火焰密封、去玻璃、淬冷、热区运行、包埋磨抛与FIB内部过程。具体原化学转移/工具、火焰对准旋转、真实热引丝/张力调节、淬冷动作、逐级磨抛与铣削轨迹未复刻
- 外部装载/夹持已展开、内部过程仍服务化：干燥/整合、PC开槽、玻璃拉丝、会聚拉丝和谱学/电子/衍射测量。操作包含冷态夹具/载具装卸、关门、外部导入、接线和条件选择；不包括源设备内部微动作
- 已展开具体手部/移动代理：棒插管、五层ASG套管、CPC插片与PC对合、中央单/双芯和两侧金属穿导口、端部剥露/接触、样品装夹/换向、半径件/卷绕/载荷承接、织物通道/板/帽/仿体/潜艇外部装配、收线归档与复位
- 上述“已展开”仍全是来源宏动作约束下的authored机器人规划。原作者夹具、抓力、公差、工具、轨迹、细微顺序通常未报告，不能将代理设定归因原作者
- 对照预制棒的详细密封法未充分报告，当前借用封闭密封接口只是任务补全，不宣称Ge/silica或Ge/BSG原实验按主路线完全相同封装

后续细粒度扩展应先补原方法/设备资料或明确使用独立静态道具代理。未知列表仍需保留；不要求为完整设计初版补现实危险配方，也不进行危险执行。
