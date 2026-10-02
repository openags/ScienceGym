# 手性超材料：整篇论文驱动的长程移动机器人任务族

> Public task-specification snapshot: source packets, scenes, models and runtime dependencies referenced below are not included. See ../../EXPORT_NOTES.md for current export boundaries. This is a design specification, not an executable or experimentally validated benchmark.

论文：Large recoverable elastic energy in chiral metamaterials via twist buckling，Nature，DOI 10.1038/s41586-025-08658-z。固定来源为已有审计保留的主文、SI、图表及七段补充视频。

## 1. 任务设计目标

本交付把整篇已报告物理工作转换为从材料货架到实验后归档清理的 TASK DESIGN。机器人必须跨工位操作材料容器、打印托盘、样品组件、装配定位器、边界夹具、加载装置及样品存储位，维持材料、对象、循环和条件身份。这不是把准备好的橡胶样品放进压板的单点演示，也不是新审计工具或CLI。

科学响应可以由明确标为mock的状态/数据夹具提供，不要求本阶段求解真实变形或预测能量。设计验收的是长程操作、依赖、对象状态、对照和异常恢复，不是强迫曲线匹配论文数值。当前没有运行机器人、物理仿真、ANSYS或真实硬件。工艺、CAD、标定未知限制未来真实执行就绪，不妨碍完整任务设计交付。

整篇是任务族。橡胶/TC4、几何/厚度/层数/边界控制可以独立抽取；一个episode可以选择一个完整分支、一个对照包或一个材料家族。不能强制创造“先橡胶后金属”的作者全局时间顺序。

## 2. Agent-visible 与 evaluator-only

### 给机器人：目标、初始场景和观察

示例任务：

> 使用实验室现有橡胶原料与设备，制备并组装指定的3×3手性格构，进行允许内部扭转的压缩和重复加载观察。将样品身份、加载/卸载记录及最终状态关联，完成后把样品保存到指定格位并恢复工位。当前使用预设mock观察和响应，目标是取得条件明确、对象状态可追踪的记录，无需预测论文的能量数值。

Agent得到所选配置参数卡/必要来源摘录、材料和设备清单、允许的设备接口与安全规则、可见标签、可查询的设备状态和过程中返回的观察（当前为预设mock反馈，始终带mock标签）。初始场景包含封闭原料匣、空构建托盘、未装配工装、空试验台及归档位，不以已经完成的试样作为默认起点。机器人需要自行规划运输、制造、装配、测试和收尾。

### 仅给评测器：路线、隐藏状态和标准

本文件后续参考操作、完整branches.json依赖、正确对象谱系、mock调度、隐藏破损/卡滞标记、终态oracle及恢复答案属于评测侧材料，不能整体给机器人当提示词。参考路线描述预期闭合流程，尚未验证机器人可达/可执行；不要求唯一轨迹；安全且等价的取放次序和路径可以接受。

硬性成功条件：

1. 从正确材料经过制造、释放；不能凭空生成样品或跳过制造
2. 需要层叠的配置确实做组件取放、对合、顶板安装和临时工装移除
3. 上机物件与材料、尺寸族及边界一致；自由扭转/锁转、有箱/无箱不能混淆
4. 加载机驱动压缩；运动时机械臂退出危险区；卸样前全卸荷并回撤
5. 数据绑定样品、条件和循环。金属初次、残余态、同件后续循环分开；四样品与同件四周期不同
6. 鼓出、逐层屈曲、低响应、接触和塑性残余是可观察的研究现象，不因偏离理想曲线自动判失败
7. 异常时安全停止、隔离/重做并保留历史；不把损伤/已循环件换标签冒充新件
8. 最终样品归档或明确隔离；机器空载，工装、余料回位，实验空间无遗留样品

对照包要求各条件均完成，变化因素和记录关联正确。6.09J等论文结果仅作为reported reference fixture，不是机器人必须实现的物理目标。一次按钮操作、一个漂亮模型或mock输出都不能证明实际科学复现。

## 3. 工位与对象流

WS_STOCK材料柜 → WS_RUBBER_PRINT或WS_TC4_PRINT材料专属打印机 → WS_POST后处理/释放 → WS_ASSEMBLY适用装配 → WS_METROLOGY质量/尺寸 → WS_TEST边界与循环 → WS_STORAGE归档/隔离 → WS_CLEAN清理复位。WS_DATA只负责非手工数据交接和比较。

实体接口包括：封闭料匣、可抓托盘、门/导轨/面板、编号分格盒、端板/环抓取区、定位梳、可逆连接片、上下压板、护罩、可拆侧箱、防转臂、相机、归档格、擦布与分类废片盒。它们是task-design surrogate，具体品牌和机械精度没有被证实。场景/粗级资产见../../scenes/chiral_scene_plan_v2/SCENE_PLAN_ZH.md（交付包内路径）。

制造全链为取料、装料和构建托盘、关门启动、收到mock完成及安全释放、取构建、后处理并释放样品。真实打印技术、原料形态、温度/层厚/固化/热处理未知。密封TC4料匣避免假定真实裸粉/线材路线；封闭后处理服务接口不等于论文已报告除粉、切割或喷砂。

全部搬运抓承压板、端环或粗节点，不用细杆承担整件重量。连接片、定位梳、方向标记、抓握位及顺序是authored。杆固定于环不授权推定作者逐杆粘接、焊接或螺钉装配。

## 4. 完整主案例：从橡胶原料到归档

### R01 橡胶手性阵列

这是一条可供移动机器人实例化的任务设计，不是作者原始操作录像，也不是物理执行声明。科学响应由标记为 mock 的状态/曲线夹具提供。操作中的运输、门把手、料匣、托盘、定位器、夹持接口、清理顺序均为本任务作者补足的连接动作。

### 样品与目标

- 来源：主文 PDF p5 Fig4a/Experiments，p9 Samples，p10 Experiments，p20 ED10a，p21 Table1 row1，Video4
- R01：橡胶圆杆手性阵列，平面3×3；单元 N=8、r=1.5 mm、R=7.5 mm、α0=5°、h0=30 mm；整件包络65×65×72 mm
- 本任务用3×3平面位置×上下镜像、18个任务半单元：ED10a两层图示与表中 Nbk=144、每单元8杆相符。这是图像＋算术支持的几何解释与任务拆件方案，不证明存在18个已知独立可拆实物件，也不是原文列出的制造BOM
- 构建目标：从橡胶专用料匣开始，制造分离单元，装配、压缩/卸载/再加载，最终将样品归档、工位复位
- 本任务将 ε=0.25 选作mock加载终点，因为它是row1的报告比较终点；它不是已知的作者全程最大加载应变。默认两次加载是任务设计值，论文总周期数未知

### 连续操作叙事

1. 在 WS_STOCK 用料匣把手拿起标为 R01 的橡胶专用料匣，放进运输托盘；再把空构建托盘放入同车另一槽。不得误取TC4料匣。橡胶配方/批次/打印技术未知，料匣是通用任务代理
2. 移动到 WS_RUBBER_PRINT。拉开打印机门，把料匣插入材料槽，把构建托盘沿导轨推到底；撤手后关门。在面板选择R01工单并按启动。工单明确要求分离手性单元，不把一整块预制阵列直接放进试验机替代制造
3. 打印机mock完成后，确认门互锁已释放，开门，抓托盘把手取出整盘，搬到 WS_POST。只有托盘与单元状态变为可触碰/可释放后才抓件；真实温度、固化时间、层厚、设备和工艺参数仍为unknown
4. 在后处理夹持座放稳托盘。按本场景的可释放接口逐件取下单元，放进R01编号分格盒。若实例启用了可拆任务支撑片，先夹持支撑片拉脱并投入指定废料盒；此支撑结构及拆除方式是authored，不声称论文采用它。任何必要真实固化/清洗/后处理配方等待外部填入，不编造化学配方
5. 把分格盒、底承压板和上承压板搬到 WS_ASSEMBLY。将底板放到3×3定位座；按(i,j)顺序抓单元刚性环，放到9个底层位置。再分别对准9列放上第二层。18次半单元取放是实际对象循环，而不是18个独立科学实验
6. 安放可拆的临时定位梳，完成场景提供的环对环可逆接合，再放上顶板；依序抽出定位梳。接合件/顺序为任务设计代理，源文连接方式未知；不臆造作者逐根胶接、焊接或螺纹装配。单元方位按场景配方标记定位，真实CAD和手性方向配合保持待定。装完后9列中间环仍独立可转，运输夹具不得跨接并锁死中间环
7. 在 WS_METROLOGY 将整件放上秤，再放到尺寸定位台，沿标示外形接触面测整体高度、投影尺寸，抓刚性环避免压软杆。记录样品身份、完整质量和尺寸；测量方式是authored连接动作，不把整件质量当成屈曲杆质量。mock读数与文献值分别保留
8. 把整件放入带底部承托的运输托盘，搬到 WS_TEST。在上压板回撤且护罩打开时，双指夹/托举底承压板取样，将其放在下压板定位区；拿走运输夹具。不安装侧向约束箱，也不安装中间环防转臂。独立扭转由样品本身的自由度提供，不假定商用旋转压头/轴承
9. 调整侧面相机朝向样品，拍下初始形态。撤出机器人末端，关护罩，在控制面板选择R01与本次循环ID，启动压缩。机器人不得用手压试样替代加载机，也不能接近运动压板。按mock任务目标加载至比较应变0.25，保存力/位移记录及独立扭转状态；这不是当前真实力学求解
10. 按卸载，等待压板解除接触。记录卸载后高度/形态，再执行同一件的第二次加载和卸载。不能将这两次任务循环叫作者真实周期1、2；橡胶表中没有专门初次加载能量，不捏造初次/重复差额
11. 全卸荷、上压板回撤并释放门互锁后开罩，托住底板，取出R01放回编号运输槽。搬到 WS_STORAGE，放入R01归档格。若发生掉落、错抓软杆或环受卡，移到隔离格并记录状态；不得继续使用原“未损伤”身份
12. 到 WS_CLEAN 卸掉临时定位梳/运输夹具并归位，收起未用料匣，清除打印支撑代理和台面碎屑，擦拭托盘及台面。清洁介质在当前设计中是干净干擦布，不虚构论文溶剂流程。关闭机门，测试压板留安全回撤状态，场地空出

### 可验收完成态

材料曾经过打印工位而非凭空出现；18个代理单元经分格转运和装配；阵列边界保持自由扭转；两次mock加载分别有加载/卸载记录；测试期间夹持器不在压板危险区；最终试样位于R01归档格、可拆工装回库、试验机空载。能量20.02 kJ/m³等论文值只可标为 reported fixture，不作为机器人已经测得的结果，也不是本任务必须预测的物理量。


## 5. TC4从制造到循环状态保存

取TC4封闭料匣和空构建盒 → 专属打印机装料、装盒、关门启动 → 制造完成取盒 → 封闭后处理单元接收构建盒、完成配方代理并安全释放 → 抓端环/端板将金属件分格。

圆杆与方梁手性件需要将下半单元放底座，对合上半单元、完成可逆接合、放顶板并抽掉临时定位工装。两层是图示支持的任务几何；真实分件/接头未知。棱柱和单层锁转件按打印成形格构/单元直接转运，不发明逐杆搭格。

称量和尺寸操作后搬至试验机。自由手性移除跨环约束；杆式棱柱安装侧箱；锁转件安装防转臂并保留轴向移动。板式棱柱具体侧箱边界未被单独明确，本任务默认无加装箱是authored选择，不是原作者无箱的事实，更不增加一个板式有/无箱实验对。

每个金属实例必须保存：新件直杆状态 → 初次加载 → 卸载后的残余塑性/α0增大/轻微杆弯曲 → 同一件幅值内再次加载/卸载 → 卸样并以已循环状态归档。初次输入面积不能全称已回收弹性能；Fig4h,j取初次加载参考值，Table1重复列另存。

ED10g的chiral1/2/3/4分别可寻址，chiral2用于主Fig4。四显示样品不等于四独立制造批次，也不是同一件四周期。默认任务物件分别建立；若与M12共享需显式identity_alias并保留循环历史。

表行16与17不合并：表行16ε=0.014，而ED10 FE等局部应力为ε=0.012；自由手性表ε=0.036，而FE点ε=0.037。均照原值保留。局部Mises应力来自FE，不是实验传感器。表行17的Nbk=21照录，与标称20杆的差异不靠删/增杆掩盖。

## 6. 全部条件家族与不可替代差异

每一行完整复用“原料→制造→释放→适用装配→计量→装夹→观察/循环→卸样→归档清理”。28条记录包含条件、重叠图表标签、四显示样品及工具演示，不是28个独立作者实验的数量声明。

|任务ID|配置与来源参数|边界/装配差异|观察、端点与身份限定|
|---|---|---|---|
|R01|rubber 手性 rod / 表行1；source_table_row=1；primitive_dimension_mm=1.5；dimension_meaning=r；envelope_mm=[65, 65, 72]；reported_comparison_strain=0.25；Nbk=144；whole_density_kg_m3=290.27；N_per_unit=8；R_mm=7.5；alpha0_deg=5；h0_mm=30；array_plan=[3, 3]|free_internal_rotation；rubber_array_3x3x2_surrogate|3×3平面、图示两层；18分件是图示与144/8支持的任务拆件解释，不是来源BOM；运输抓底板/刚性环，取下所有跨环运输夹具；不安装防转臂和侧箱；mock终点=0.25|
|R02|rubber 棱柱 rod / 表行2；source_table_row=2；primitive_dimension_mm=1.5；dimension_meaning=r；envelope_mm=[100, 130, 100]；reported_comparison_strain=0.25；Nbk=160；whole_density_kg_m3=222.46；prism_theta_deg=40；parallel_rod_spacing_mm=10|lateral_box；printed_single_object|两层面内曲线与主图关联，但R_PRISM_L2及row2物件是否相同未证实；默认任务实例分开；mock终点=0.25|
|R03|rubber 八面体 rod / 表行3；source_table_row=3；primitive_dimension_mm=1.5；dimension_meaning=r；envelope_mm=[104, 104, 151]；reported_comparison_strain=0.25；Nbk=216；whole_density_kg_m3=85.05|no_added_box_authored；printed_single_object|逐层非同步屈曲是保留的观察类别，不把真实失稳纠正成同步运动；Video6未给半径；不能声称此视频分别拍过r1.5和r2两支；mock终点=0.25|
|R04|rubber 八面体 rod / 表行4；source_table_row=4；primitive_dimension_mm=2；dimension_meaning=r；envelope_mm=[104, 104, 151]；reported_comparison_strain=0.25；Nbk=216；whole_density_kg_m3=111.38|no_added_box_authored；printed_single_object|逐层非同步屈曲是保留的观察类别，不把真实失稳纠正成同步运动；Video6未给半径；不能声称此视频分别拍过r1.5和r2两支；mock终点=0.25|
|R05|rubber Kelvin rod / 表行5；source_table_row=5；primitive_dimension_mm=1.5；dimension_meaning=r；envelope_mm=[185, 185, 205]；reported_comparison_strain=0.25；Nbk=176；whole_density_kg_m3=10.6|no_added_box_authored；printed_single_object|即使能量极小也执行完整制造、上机、卸样链；不因响应小判成遗漏/失败；不强制理想一阶弯曲模式；mock终点=0.25|
|R06|rubber Kelvin rod / 表行6；source_table_row=6；primitive_dimension_mm=2；dimension_meaning=r；envelope_mm=[185, 185, 205]；reported_comparison_strain=0.25；Nbk=176；whole_density_kg_m3=17.55|no_added_box_authored；printed_single_object|即使能量极小也执行完整制造、上机、卸样链；不因响应小判成遗漏/失败；不强制理想一阶弯曲模式；mock终点=0.25|
|R07|rubber 棱柱 plate_thickness / 表行7；source_table_row=7；primitive_dimension_mm=3.2；dimension_meaning=t；envelope_mm=[20, 52, 44]；reported_comparison_strain=0.25；Nbk=4；whole_density_kg_m3=517.92|no_added_box_authored；printed_single_object|板式棱柱的侧箱边界未被单独明确；默认无加装侧箱是任务选择，若补入真实配方可替换，不能据此声称原作者无箱；不得与杆式棱柱混为同一几何；mock终点=0.25|
|R08|rubber 张拉整体 rod / 表行8；source_table_row=8；primitive_dimension_mm=1.5；dimension_meaning=r；envelope_mm=[94, 94, 110]；reported_comparison_strain=0.4；Nbk=48；whole_density_kg_m3=18.11|no_added_box_authored；printed_single_object|四个半径必须分别实例化；Video7不绑定某一半径；0.4是报告比较终点；超过0.4的邻杆接触限定应保留；mock终点=0.4|
|R09|rubber 张拉整体 rod / 表行9；source_table_row=9；primitive_dimension_mm=2；dimension_meaning=r；envelope_mm=[94, 94, 110]；reported_comparison_strain=0.4；Nbk=48；whole_density_kg_m3=32.2|no_added_box_authored；printed_single_object|四个半径必须分别实例化；Video7不绑定某一半径；0.4是报告比较终点；超过0.4的邻杆接触限定应保留；mock终点=0.4|
|R10|rubber 张拉整体 rod / 表行10；source_table_row=10；primitive_dimension_mm=2.5；dimension_meaning=r；envelope_mm=[94, 94, 110]；reported_comparison_strain=0.4；Nbk=48；whole_density_kg_m3=49.28|no_added_box_authored；printed_single_object|四个半径必须分别实例化；Video7不绑定某一半径；0.4是报告比较终点；超过0.4的邻杆接触限定应保留；mock终点=0.4|
|R11|rubber 张拉整体 rod / 表行11；source_table_row=11；primitive_dimension_mm=3；dimension_meaning=r；envelope_mm=[94, 94, 110]；reported_comparison_strain=0.4；Nbk=48；whole_density_kg_m3=70.37|no_added_box_authored；printed_single_object|四个半径必须分别实例化；Video7不绑定某一半径；0.4是报告比较终点；超过0.4的邻杆接触限定应保留；mock终点=0.4|
|M12|TC4 手性 rod / 表行12；source_table_row=12；primitive_dimension_mm=0.6；dimension_meaning=r；envelope_mm=[20, 20, 64]；reported_comparison_strain=0.036；Nbk=40；whole_density_kg_m3=593.75；N_nominal_per_unit=20；R_mm=7.5；alpha0_deg=5；h0_mm=30|free_internal_rotation；tc4_two_layer_surrogate|先装两层再上机，NBk40与20/层相符；可拆分界面仍为authored；第一次加载与残余态、后续循环分开；mock终点=0.036|
|M13|TC4 手性 square_beam_b_equals_t / 表行13；source_table_row=13；primitive_dimension_mm=1.2；dimension_meaning=b=t；envelope_mm=[20, 20, 64]；reported_comparison_strain=0.036；Nbk=40；whole_density_kg_m3=621.09|free_internal_rotation；tc4_two_layer_surrogate|先装两层再上机，NBk40与20/层相符；可拆分界面仍为authored；第一次加载与残余态、后续循环分开；mock终点=0.036|
|M14|TC4 棱柱 rod / 表行14；source_table_row=14；primitive_dimension_mm=0.6；dimension_meaning=r；envelope_mm=[25, 105, 45]；reported_comparison_strain=0.036；Nbk=64；whole_density_kg_m3=456.3；prism_theta_deg=40；parallel_rod_spacing_mm=3|lateral_box；printed_single_object|；mock终点=0.036|
|M15|TC4 棱柱 plate_thickness / 表行15；source_table_row=15；primitive_dimension_mm=1.2；dimension_meaning=t；envelope_mm=[20, 52, 44]；reported_comparison_strain=0.036；Nbk=4；whole_density_kg_m3=718.97|no_added_box_authored；printed_single_object|板式棱柱的侧箱边界未被单独明确；默认无加装侧箱是任务选择，若补入真实配方可替换，不能据此声称原作者无箱；不得与杆式棱柱混为同一几何；mock终点=0.036|
|M16|TC4 锁转手性/非手性弯曲 rod / 表行16；source_table_row=16；primitive_dimension_mm=0.6；dimension_meaning=r；envelope_mm=[20, 20, 32]；reported_comparison_strain=0.014；Nbk=20；whole_density_kg_m3=593.75；N_nominal_per_unit=20；R_mm=7.5；alpha0_deg=5；h0_mm=30|rotation_locked；printed_single_object|防转约束施加于环自由度，不把所有chiral列统一锁死；row16和17是否复用同物件未知；任务默认分开新件以保持初次历史可追踪；表ε0.014保留；ED10 FE等应力ε0.012另存，不合并或修正；mock终点=0.014|
|M17|TC4 锁转手性/非手性弯曲 rod / 表行17；source_table_row=17；primitive_dimension_mm=0.6；dimension_meaning=r；envelope_mm=[20, 20, 32]；reported_comparison_strain=0.036；Nbk=21；whole_density_kg_m3=593.75；N_nominal_per_unit=20；R_mm=7.5；alpha0_deg=5；h0_mm=30|rotation_locked；printed_single_object|防转约束施加于环自由度，不把所有chiral列统一锁死；row16和17是否复用同物件未知；任务默认分开新件以保持初次历史可追踪；原表Nbk=21照录；与标称20杆几何的差异不得用删/增杆来掩盖；mock终点=0.036|
|R_SMALL20|20°橡胶小型手性件；alpha0_deg=20；R_mm=5.5；rod_diameter_mm=1.8；h0_mm=20；force_axis=4 × F1rod (N)|free_internal_rotation；printed_single_object|不是30mm主样品；本mock选0.25，仅作任务终点，作者完整协议未知；mock终点=0.25|
|R_SMALL50|50°橡胶小型手性件及接触观察；alpha0_deg=50；R_mm=6；rod_diameter_mm=1.7；h0_mm=20；force_axis=4 × F1rod (N)；reported_contact_above_strain=0.3|free_internal_rotation；printed_single_object|mock选0.35以包含ε>0.3接触状态；该终点是authored，不是作者已报告最大值；接触是研究现象而非强制修复的失败；接触后结果不可外推为无接触模型验证；mock终点=0.35|
|R_PRISM_L1|一层橡胶棱柱面内控制；layers=1；one_layer_structure=two half metacells|no_added_box_authored；printed_single_object|保持一层和两个半元胞的几何；确切侧夹具未知，单层默认无箱为设计选择；mock终点=0.25|
|R_PRISM_L2|两层橡胶棱柱面内控制；layers=2|lateral_box；printed_single_object|和row2保留条件关联，默认独立任务物件，不伪造物件复用证据；mock终点=0.25|
|R_PRISM_L4|四层橡胶棱柱面内控制；layers=4|lateral_box；printed_single_object|ED9c明确四层入箱，不能只做最终两层控制；mock终点=0.25|
|R_PRISM_UNBOXED|两层橡胶棱柱无侧约束鼓出；layers=2|unboxed_control；printed_single_object|试验前将侧箱壁搬回架上，保留横向自由空间；不要为了表现好而把鼓出样品重新限制；无箱与箱内曲线必须分开；mock终点=0.25|
|R_TOOL_DEMO|Video5可见工具交互独立演示；|unboxed_control；printed_single_object|Video5约4.66–5.50秒有靠近/交互/退出；工具身份、方向/力度/目的及定量曲线关联未知；另设演示物件和隔离记录；不把干预混入R_PRISM_UNBOXED的纯比较记录；mock使用无刃软端探针和离散接触事件，仅补动作接口，不归因为作者诱发失稳；mock终点=fixture终止事件|
|M_CHIRAL1|TC4 displayed sample chiral 1；source_trace_label=chiral 1；source_used_in_main_Fig4=False|free_internal_rotation；tc4_two_layer_surrogate|四样品显示与同件重复循环是两类不同重复；采用M12几何作任务代理，真实每条曲线完整几何/制造批次对应未知；若与M12共用对象须先提供明确identity_alias，默认不声称同一对象；mock终点=fixture终止事件|
|M_CHIRAL2|TC4 displayed sample chiral 2；source_trace_label=chiral 2；source_used_in_main_Fig4=True|free_internal_rotation；tc4_two_layer_surrogate|四样品显示与同件重复循环是两类不同重复；采用M12几何作任务代理，真实每条曲线完整几何/制造批次对应未知；若与M12共用对象须先提供明确identity_alias，默认不声称同一对象；mock终点=fixture终止事件|
|M_CHIRAL3|TC4 displayed sample chiral 3；source_trace_label=chiral 3；source_used_in_main_Fig4=False|free_internal_rotation；tc4_two_layer_surrogate|四样品显示与同件重复循环是两类不同重复；采用M12几何作任务代理，真实每条曲线完整几何/制造批次对应未知；若与M12共用对象须先提供明确identity_alias，默认不声称同一对象；mock终点=fixture终止事件|
|M_CHIRAL4|TC4 displayed sample chiral 4；source_trace_label=chiral 4；source_used_in_main_Fig4=False|free_internal_rotation；tc4_two_layer_surrogate|四样品显示与同件重复循环是两类不同重复；采用M12几何作任务代理，真实每条曲线完整几何/制造批次对应未知；若与M12共用对象须先提供明确identity_alias，默认不声称同一对象；mock终点=fixture终止事件|

## 7. 对照包、循环与数据交接

- 橡胶几何包：R01–R11。保留圆杆棱柱与板式棱柱、八面体两个半径、Kelvin两个半径及张拉整体四个半径。R01–R07的表能量比较端点为0.25，R08–R11为0.4，不能称全部同全局应变比较
- 层数/侧约束包：R_PRISM_L1/L2/L4比较面内变形，另将两层有箱与R_PRISM_UNBOXED鼓出比较。单层由两个半元胞构成。四层盒内不是可删的重复数据；无箱控制不因失稳而被修成有箱
- Video5工具演示：R_TOOL_DEMO单独制造/保留对象。按“取软端代理工具→靠近→符号接触→退回→放回”保留可见手工动作。4.66–5.50秒只是视频定位，不是工具运动时间；目的、力、方向、量化曲线关联仍unknown。任何真实带载接近需另行工程安全设计；当前不绕过护罩
- 小件包：R_SMALL20与R_SMALL50使用各自几何和20mm参考高；图中力轴是4×F1rod。50°的ε>0.3接触必须可被记录；本任务选0.35作mock示范终点，不声称源文加载协议
- TC4几何/循环包：M12–M17保留初次/卸载残余/重复列。M_CHIRAL1–4是显示样品身份，可单独抽样评测；不必全放进一个长episode
- TC4边界包：M12自由转动与M16/M17锁转不同端点分别汇合。等全局应变和等局部应力是两种比较；局部应力参考来自非手工FE分支

数据包至少包含object_id、component_ids、material、condition_id、boundary、geometry_basis、cycle_id/phase、force/displacement（mock或实测类型）、image/state、reference_height、area/volume_basis、whole_mass、buckling_mass_basis和source_tag。没给出的值保持null/unknown，不能把文献值填入新测量字段。

等效应变/应力、刚度、平台强度、体积能量与能量/屈曲部件质量属于非手工计算。整件质量包含不屈曲部分，不能代替屈曲质量分母。初次能量、重复加载能量与卸载可恢复量的语义分开；当前不通过重积分/拟合伪造作者原始轨迹。

## 8. 失败与恢复是任务的一部分

|可观察异常|允许恢复|必须保持的事实|
|---|---|---|
|料匣键位不符/材料标签不符|取回放原槽，换正确材料；若已制造则错件隔离|不只换标签，不让错误材料过关|
|打印完成后缺一个组件|将缺件位标记，重新制造替换组件并关联新的component_id|不能凭空补件或跳过构建依赖|
|抓软杆造成变形或掉落|停止、托住可承力部位，移隔离格并补制新件|损伤对象保留原身份，不继续当未损伤新件|
|定位梳/运输夹具跨接中间环|在空载状态卸下，必要时退回装配台|自由扭转不能依赖更大力挤开约束|
|错装侧箱或锁转臂|启动前拆回工装架，按条件重设|数据不能在错误边界下仍标正确条件|
|相机遮挡|移相机重拍初态或当前状态|不改变已锁定边界来改善取景|
|鼓出/逐层失稳/低响应/50°接触|保留观察，按任务端点与安全事件卸载|这些可能是研究结果，不自动“维修”成理想模式|
|采集丢失|停止并保存无效段；重做需产生新run/cycle身份|金属首循环丢失后不能把下一周期冒充初次；需新件才能重取首循环|
|卸载后仍夹滞|保持护罩关闭，确认全卸荷；解除可拆代理约束后托举|不边撬边计回收能量，不手伸运动压板|
|归档格被占|使用分支备用格或隔离格|不覆盖他件身份，不把已循环件重置为新件|

任务可用显式、可观测故障测试规划恢复，但不以对agent不可见且不可查询的故障要求不可能推断。隐藏oracle只判真实状态；所需辨识信号通过标签、设备错误或观察反馈暴露。

## 9. 理论/非手工部分的处理

77个来源覆盖单元全部进入coverage_matrix.json，但不都算动手操作。理论、FE与分析分别保留：垂直/缺陷杆屈曲，斜杆与归一化，一般3D手性线性关系，面内/面外弯曲、杆内扭转、轴压及螺旋修正，半径/角度/厚度比较，粗杆边界，两种非线性微极模型，三种分步FE控制，格构/截面数值比较，以及TC4等应力/等应变FE。

这些内容在nonmanual_scope.json是参考输入/数据交接，无需机器人制造一个“2°缺陷杆实验”。Videos1–3是数值展示，不增加交叉梁、扁宽梁的已报告实物制造分支。SI没有补出新的制备配方。低频隔振、冲击防护、执行器/扭转调制、跳跃或储能器件属于提议应用，没有独立实物实验可转换，明确排除。

Methods和Fig3的设计依据可影响配置卡，但不能伪造原作者的完整参数搜索历史。已显示的图表关系与任务作者安排的操作依赖也不能混为真实作者时间线。

## 10. 未知参数不删步骤

CAD、打印工艺、配方/批次、后处理、装配接头、真实侧箱/锁转细节、速率/预载/标定/采样/总循环数、原始测量轨迹及Video5工具目的均保持unknown。当前每项都有操作接口、状态输入/输出和显式代理，见unknown_parameters.json。它们不阻止设计覆盖完成；未来实体执行需工程配置和验证，当前不声称就绪。

本目录文件：

- TASK_DESIGN.md：自包含任务族、主案例、条件差异、失败恢复、操作及覆盖附录
- FIRST_ROUTE_RUBBER.md：单独可读的端到端橡胶案例
- operations.json：带对象、位置、前置/动作/后置、恢复及来源标签的操作模板
- branches.json：完整条件参数、物件/循环绑定、装配/边界差异及全链顺序
- assets.json：操作目标/抓取接口需求，具体场景文件在同级chiral_scene_plan_v2
- dependencies.json：分支内材料/动作依赖及跨条件数据汇合；无伪造全局作者时间线
- coverage_matrix.json：原77来源单元逐项映射，动手/混合/非手工显式分类
- nonmanual_scope.json：理论、FE、分析及应用提议的独立归类
- unknown_parameters.json / mock_contract.json：未知与代理、事件接口和不允许推断
- provenance.json / design_validation.json：输入哈希和一次性静态完整性检查，不是新的CLI

## 附录A：完整操作合同（设计初版，未验证可达/可执行）

下列是评测侧参考动作。{branch}绑定到上一节每个条件自己的物件和参数；material_printer按材料解析到对应打印工位。按条件的operation_sequence挑选实际动作，不能把所有夹具动作都套到所有样品。动作是模板，遍历18个任务半单元或同件循环是对象操作次数，不是科学实验数量。


### FAB01 拿取专属原料与空构建托盘

位置：WS_STOCK；目标：material_cartridge, transport_tray, build_tray；对象：本branch物件/条件ID

前置：branch material and object identity bound；empty cart slots

操作：抓料匣把手，从橡胶或TC4指定货格取出封闭料匣放入运输槽；把空构建托盘推入另一槽，驾车到该材料打印工位

后置：correct material cartridge and tray at selected printer；no TC4/rubber cross-use

恢复：错料未装机则放回原格重新取料；身份不明料匣进入隔离区

来源与设计：论文采用橡胶和TC4材料3D打印。具体抓握/运输/机构/按钮/离散状态为authored连接。未知：原料形态、配方、批次及供应商

### FAB02 打开打印舱并装入料匣

位置：material_printer；目标：printer_door, material_cartridge, material_port；对象：本branch物件/条件ID

前置：printer idle；door interlock released；FAB01 done

操作：握门把手打开舱门；沿场景键槽推入料匣直至到位；关闭独立供料盖

后置：material cartridge docked；no loose stock on floor

恢复：料匣卡滞则退回托盘；不要带力硬插或拆开TC4密封匣

来源与设计：材料专属3D打印存在。具体抓握/运输/机构/按钮/离散状态为authored连接。未知：真实打印工艺及设备；不推定熔融/树脂/粉床技术

### FAB03 放入构建托盘并启动本分支打印

位置：material_printer；目标：build_tray, printer_door, printer_panel；对象：本branch物件/条件ID

前置：FAB02 done；branch build recipe surrogate available

操作：握托盘把手推入构建导轨；撤手关舱门，在面板选择本branch构建工单并按启动

后置：machine in printing state；build job binds components to object lineage

恢复：门未关不启动；选错工单在制造前取消重选；已制造错件隔离，不换标签

来源与设计：分离手性单元和其他杆/梁/板格构通过3D打印制造。具体抓握/运输/机构/按钮/离散状态为authored连接。未知：CAD、打印朝向、层厚、温度/功率、速度及支撑均unknown

### FAB04 从打印舱取出完成的构建托盘

位置：material_printer；目标：printer_door, build_tray, printed_components；对象：本branch物件/条件ID

前置：print fixture emits completed；safe_to_touch and door_release events；not based on elapsed wall-clock alone

操作：开门，抓托盘把手沿导轨抽出；保持托盘水平放入运输槽，移到后处理台

后置：completed build at WS_POST；manufacturing stage cannot be skipped

恢复：缺件/断件连托盘转隔离；仅在外部mock工单授权的新构建中重打并产生新lot/object ID

来源与设计：打印阶段有已制备样品输出。具体抓握/运输/机构/按钮/离散状态为authored连接。未知：实际冷却、固化、除粉及释放时间

### POST_R 橡胶件释放与分格

位置：WS_POST；目标：build_tray, post_holder, release_tabs, component_tray；对象：本branch物件/条件ID

前置：rubber branch；FAB04 done；safe_to_release event

操作：把构建托盘锁入后处理定位座；若本设计启用支撑片，夹片从预制易脱接口取下投入对应废料盒；抓单元环或格构刚性节点，从托盘取下并逐件放入编号分格盒

后置：rubber components free and sorted；unused/removed supports in bin

恢复：薄杆被压扁/撕裂则停止抓杆，改抓环；损伤件隔离并重制替换，保留原号

来源与设计：原文只证明橡胶3D打印，未报告释放方法。具体抓握/运输/机构/按钮/离散状态为authored连接。未知：真实清洗、固化、脱模/支撑流程；任务可拆片不是来源事实

### POST_M TC4构建转入封闭后处理并取件

位置：WS_POST；目标：build_tray, closed_post_cell, post_panel, component_tray；对象：本branch物件/条件ID

前置：TC4 branch；FAB04 done

操作：把构建盒插入封闭后处理单元并关门；按本工单的后处理按钮；mock以完成事件释放样品，真实配方外部注入；仅在安全释放后取出内托盘，抓刚性端环/端板，将金属件放入编号槽

后置：metal components released with no loose process media；postprocessing state retained in lineage

恢复：后处理未释放不绕过门锁；样品有毛刺/残余支撑标志则退回加工等待，不能上试验机

来源与设计：TC4打印存在；后处理接口是合理任务连接。具体抓握/运输/机构/按钮/离散状态为authored连接。未知：不能声称作者使用特定除粉、热处理、切割或喷砂；温度/残留判据待定

### ASM01 铺设底板与装配定位器

位置：WS_ASSEMBLY；目标：base_plate, assembly_nest, alignment_comb；对象：本branch物件/条件ID

前置：released components at assembly station；assembly recipe bound

操作：将底承压板放入装配台定位座；把临时定位梳插入定位孔，搬分格件盒到伸手区

后置：base plate supported；component slots accessible

恢复：定位座摆错时先抬起底板重新定位；不得用弯杆抵住定位

来源与设计：分离手性单元需组装成层叠结构。具体抓握/运输/机构/按钮/离散状态为authored连接。未知：真实定位/连接工装

### ASM02 放置第一层分离单元

位置：WS_ASSEMBLY；目标：chiral_unit, base_plate, assembly_nest；对象：本branch物件/条件ID

前置：ASM01 done；bottom slots empty

操作：按配方坐标从分格盒抓取单元刚性环；保持方位标记朝向对应符号，竖直落到各底层承接位并释放

后置：bottom layer occupied；no bending-member gripped or broken

恢复：错方向未接合则提起重放；掉落转隔离；补件使用新组件ID

来源与设计：图示层叠手性；橡胶3×3平面阵列。具体抓握/运输/机构/按钮/离散状态为authored连接。未知：真实制造分件边界与手性配对方向

### ASM03 堆叠第二层与对合接口

位置：WS_ASSEMBLY；目标：chiral_unit, interface_ring, alignment_comb；对象：本branch物件/条件ID

前置：ASM02 done；matching upper pieces

操作：抓上层端环，对准已放下层的接合位；按任务配方的镜像/方向标记落座；暂时保留定位梳以防倾倒

后置：two-layer arrangement stable；each pair has declared lineage

恢复：无法落座先提回托盘并校正；不得扭曲杆强行拼合

来源与设计：Fig4a/b及ED10a/b/c显示层叠；原文从分离单元组装。具体抓握/运输/机构/按钮/离散状态为authored连接。未知：分件数量、真实连接形式；18=144/8为图示支持的任务拆件

### ASM04 完成可逆接合并安放顶板

位置：WS_ASSEMBLY；目标：interface_ring, cap_plate, surrogate_clip；对象：本branch物件/条件ID

前置：ASM03 done

操作：在粗大环的任务接口扣入可逆连接片，不逐杆粘接；抓顶承压板，对齐端部座并放下，使其承托全部列端面

后置：assembly can be lifted by designated support；interfaces seated

恢复：接合未到位取下顶板重做；不得用永久胶/焊接填补未知

来源与设计：层叠结构组装存在。具体抓握/运输/机构/按钮/离散状态为authored连接。未知：接头/紧固力矩/胶接焊接均未报告

### ASM05 抽掉临时定位工装并释放中间环

位置：WS_ASSEMBLY；目标：alignment_comb, transport_support, interface_ring；对象：本branch物件/条件ID

前置：ASM04 done

操作：依序抽出定位梳并放回工具架；装仅托住底板的运输支架，不跨接中间环；整理上方可抓空间

后置：independent middle-ring degrees of freedom remain unbridged；fixture removed from deforming volume

恢复：工装难拔先回托底板再卸力，不拉薄杆；锁死则重新拆除后再运输

来源与设计：手性变形需相对扭转；不等于商用旋转压头。具体抓握/运输/机构/按钮/离散状态为authored连接。未知：

### MET01 将样品放秤并取回

位置：WS_METROLOGY；目标：balance, specimen, weighing_tray；对象：本branch物件/条件ID

前置：finished specimen；scale empty；mock mass fixture bound

操作：将空托盘放秤归零；托住端板/刚性节点把样品放在托盘中央，读取示值并拿回编号托盘

后置：whole_mass measured_mock field distinct from published and buckling mass；sample not squeezed

恢复：量程/漂移错误则保持样品并标readout_invalid；不能抄文献数冒充新测量

来源与设计：论文区分整件密度和屈曲部件质量；称量操作未报道。具体抓握/运输/机构/按钮/离散状态为authored连接。未知：作者称量方法和校准

### MET02 在尺寸座测量外形与参考高度

位置：WS_METROLOGY；目标：measurement_nest, caliper, specimen；对象：本branch物件/条件ID

前置：MET01 done

操作：把样品放尺寸座，用测量尺/卡尺接触端板外缘，记录长宽整体高度；取回样品；将单元h0/杆L0与整体H分别保留，不对软杆施加夹持载荷

后置：reference H/A/V lineage declared；caliper returned

恢复：软体被夹变形则松开重新非压迫读数；测不到就unknown，不强填h0=整体H

来源与设计：整件及单元归一化是不同分母。具体抓握/运输/机构/按钮/离散状态为authored连接。未知：真实几何测量方式、误差和屈曲质量分母来源

### TEST01 托盘运送样品到试验台

位置：WS_TEST；目标：transport_tray, specimen, tester_stage；对象：本branch物件/条件ID

前置：specimen prepared；machine unloaded and stopped

操作：将样品端板置于运输托架，收回机械臂并移动至试验台；把运输托盘放装样待放区，机械臂从侧面接近

后置：sample staged at tester；identity persists across transport

恢复：倾倒或碰撞则托盘转隔离，结束该未损伤分支

来源与设计：必须装入压缩装置；运输路线为authored。具体抓握/运输/机构/按钮/离散状态为authored连接。未知：

### TEST02 开罩回撤压板并清空装样区

位置：WS_TEST；目标：guard, tester_panel, upper_platen, removable_fixture；对象：本branch物件/条件ID

前置：machine idle and zero stored-load event；sample outside machine

操作：在面板执行安全回撤；开护罩，把上一个条件的侧箱壁/防转臂取下放架上，擦除接触面可见碎屑

后置：clear loading volume；no inherited boundary from previous branch

恢复：未卸荷不伸手；传感器/互锁不一致则停止当前物理接口而非跳过阶段

来源与设计：压缩边界控制存在；安全装样流程为authored。具体抓握/运输/机构/按钮/离散状态为authored连接。未知：

### TEST03 将试样落座下压板

位置：WS_TEST；目标：specimen, lower_platen, transport_support；对象：本branch物件/条件ID

前置：TEST02 done；upper clearance adequate

操作：抓底端板/环或双侧粗节点，将样品放到下压板中心的任务定位标记；解除运输托架并移出加载区域，不把夹持器当作边界约束

后置：sample seated with declared orientation；robot released specimen

恢复：未坐稳提起重放；不得用压板强行压平歪斜样品

来源与设计：试样位于相对加载表面间。具体抓握/运输/机构/按钮/离散状态为authored连接。未知：

### BND_BOX 安装侧向约束箱

位置：WS_TEST；目标：lateral_box_base, removable_box_walls, specimen；对象：本branch物件/条件ID

前置：TEST03 done；branch requires lateral_box

操作：从工装架拿对应高度的侧壁，逐片插入底框槽；闭合任务锁扣；顶部压板行程保持通畅，侧壁在目标横向方向抑制鼓出

后置：boxed condition set；loading direction unblocked

恢复：错用高度/侧壁接触加载行程则拆回对应槽，换正确版本

来源与设计：p10、ED9c和ED10e支持侧箱约束。具体抓握/运输/机构/按钮/离散状态为authored连接。未知：箱间隙、摩擦、固定形式；不可把任务值说成原文

### BND_FREE 移除跨环约束并保持手性自由度

位置：WS_TEST；目标：interface_ring, transport_clip, rotation_lock；对象：本branch物件/条件ID

前置：TEST03 done；branch free_internal_rotation

操作：将残余运输卡扣/防转臂从环附近拿走放工装架；撤出临时侧支撑，保留端面承压和内部环相对转动空间

后置：free internal twist boundary；no added rotary platen claim

恢复：发现环卡住则卸样返回装配台，不能靠更大压缩强迫扭转

来源与设计：可转手性变形边界。具体抓握/运输/机构/按钮/离散状态为authored连接。未知：

### BND_LOCK 装入防转工装

位置：WS_TEST；目标：rotation_lock, specimen_end_ring, fixture_socket；对象：本branch物件/条件ID

前置：TEST03 done；locked-chiral branch

操作：从架上拿防转臂，将其键接到任务端环接口与机架座；扣上可逆锁片，保持轴向压缩行程而约束相对转动

后置：rotation_locked condition；not mislabeled free chiral

恢复：锁片不到位则卸下重装；未解决则该条件无有效输出

来源与设计：非可转手性件出现非手性弯曲。具体抓握/运输/机构/按钮/离散状态为authored连接。未知：原作者锁转夹具形式未知；滑动键连接是代理

### BND_OPEN 移走侧箱保持开放侧面

位置：WS_TEST；目标：removable_box_walls, tool_rack；对象：本branch物件/条件ID

前置：TEST03 done；unboxed or no-added-box branch

操作：若侧壁仍在加载区则逐片取出放回架上；把相机和工具架移到外侧，使横向鼓出/逐层屈曲不撞到任务家具

后置：lateral deformation region clear；boundary explicitly open

恢复：侧面仍碰触工装则停止并移除，不把干涉当材料行为

来源与设计：无侧约束棱柱是报告控制；其他无加箱选择依branch说明。具体抓握/运输/机构/按钮/离散状态为authored连接。未知：

### OBS01 摆相机并拍初始形态

位置：WS_TEST；目标：camera, camera_stand, specimen；对象：本branch物件/条件ID

前置：boundary set；machine idle

操作：调相机支架使视野包括全部层和端板；拍下当前形态：材料/样品/循环/边界ID和手性角、杆形、层状态

后置：initial image fixture linked；camera outside moving volume

恢复：遮挡则移动相机重拍，不转动已设定边界的样品

来源与设计：论文包含变形图像/视频；相机型号和摆放方式未知。具体抓握/运输/机构/按钮/离散状态为authored连接。未知：

### TEST04 关罩并设加载程序

位置：WS_TEST；目标：guard, tester_panel；对象：本branch物件/条件ID

前置：OBS01 done；robot retracted from pinch zone

操作：关护罩；在面板选branch及condition，设本任务给定endpoint事件/应变与循环标记；保持速度/采样率为unknown参数槽

后置：guard closed；mock cycle armed；scientific recipe not fabricated

恢复：控制ID错误则启动前清除重选；真实模式遇缺配方不可运行，但任务设计仍保留完整动作

来源与设计：循环压缩有来源；具体控制输入为任务选择。具体抓握/运输/机构/按钮/离散状态为authored连接。未知：速率、预载、保载时间、采样率、标定和停止容差

### LOAD 触发一次压缩并记录变形

位置：WS_TEST；目标：tester_panel, upper_platen, camera；对象：本branch物件/条件ID

前置：TEST04 done；load identity bound；guard closed

操作：按开始压缩按钮；机器人停在压板危险区外；由mock加载机沿轴向缩小压板间距至branch目标事件，同时接收力/位移/图像事件

后置：load segment stored for this object/cycle/boundary；observed mode retained without forcing ideality

恢复：错边界/物体滑脱/掉落触发停止；若是目标鼓出、接触或非同步屈曲，则保留为正常观察，不判失败

来源与设计：压缩屈曲及形变观察是来源事实。具体抓握/运输/机构/按钮/离散状态为authored连接。未知：比较应变不是完整真实加载终点；曲线与速度不由视频秒数推定

### UNLOAD 卸载并拉开压板

位置：WS_TEST；目标：tester_panel, upper_platen；对象：本branch物件/条件ID

前置：load terminal event；guard closed

操作：按卸载，使上压板回撤直到外部载荷解除；继续记录卸载段，待zero_load及safe_clearance事件后结束循环

后置：unloading segment separate from loading；safe unloaded specimen state

恢复：卸载中夹滞则保持护罩关闭并停止驱动；不可边撬样边计回收能量

来源与设计：循环压缩及橡胶回弹、TC4卸载有来源；视频不全显示每件卸载。具体抓握/运输/机构/按钮/离散状态为authored连接。未知：

### OBS_RESIDUAL 拍卸载残余态

位置：WS_TEST；目标：camera, specimen, tester_panel；对象：本branch物件/条件ID

前置：UNLOAD done；no external load

操作：保持机内位置拍端环、杆形和残余高度；金属分别写入初次卸载后的残余塑性/α0改变；橡胶保留当前恢复程度，不覆盖为完美复原

后置：post-unload state exists；pristine state not reused after metal first cycle

恢复：未卸荷照片不能冒充残余态；重等卸荷事件再拍

来源与设计：TC4初次循环残余塑性与角度增大是来源事实。具体抓握/运输/机构/按钮/离散状态为authored连接。未知：

### RELOAD 同一物件后续压缩/卸载

位置：WS_TEST；目标：tester_panel, camera, specimen；对象：本branch物件/条件ID

前置：UNLOAD and OBS_RESIDUAL done；same object remains seated；cycle_index incremented

操作：不取换试样，在面板选下一循环，保持本条件边界和目标幅度；再次执行LOAD→UNLOAD→OBS_RESIDUAL，分别存段；默认总2周期是authored最小示范

后置：repeat segment separately addressable；same object lineage for repeats

恢复：换了对象或幅值就创建新condition/run，不把它叫原同件重复

来源与设计：后续循环的可重复性有来源；总周期数未知。具体抓握/运输/机构/按钮/离散状态为authored连接。未知：重复数、长期疲劳/耐久性未报告

### TEST_REMOVE 开罩托住样品并卸下

位置：WS_TEST；目标：guard, specimen, rotation_lock, box_walls, transport_tray；对象：本branch物件/条件ID

前置：UNLOAD completed；safe_clearance and zero_load；guard release

操作：开罩，先托住底板/粗节点，再解除防转夹或拆开侧箱可拆壁；将样品竖直提起放入原编号运输槽，撤出机械臂

后置：machine empty；object retains complete cycle history

恢复：样品附着不强拽；重新全卸荷，侧向解除代理接触后托举；损伤隔离

来源与设计：卸样是闭合流程的authored连接动作。具体抓握/运输/机构/按钮/离散状态为authored连接。未知：

### ARCHIVE 把样品送入编号归档格

位置：WS_STORAGE；目标：transport_tray, archive_slot, quarantine_slot；对象：本branch物件/条件ID

前置：TEST_REMOVE done

操作：搬托盘到对应材料架；将完整样品放归档格，金属标签保留cycled/residual；干预演示件放演示专用格；损伤/历史不明件放隔离格

后置：sample archived or quarantined；no reclassification as pristine

恢复：格位被占则用该branch备用格，不能覆盖其他样品身份

来源与设计：作者具体存储未报告；保留状态是任务要求。具体抓握/运输/机构/按钮/离散状态为authored连接。未知：

### CLEAN01 清掉工位碎屑并归还工装

位置：WS_CLEAN；目标：dry_wipe, waste_bins, tool_rack, transport_tray；对象：本branch物件/条件ID

前置：machine unloaded；sample archived

操作：将支撑代理/废片按材料分入废料盒；用干净干擦布擦托盘、装配台和压板可触区域；将定位梳、侧箱壁、防转臂、相机工具归还标记格位

后置：empty clean work surfaces；tools stowed；no specimen disposed accidentally

恢复：不明残留保持封闭并隔离处理；不擅用溶剂/压缩空气清TC4工艺粉末

来源与设计：收尾由任务作者补全，论文未描述清洁配方。具体抓握/运输/机构/按钮/离散状态为authored连接。未知：

### CLEAN02 回收余料并复位机器

位置：WS_CLEAN；目标：material_cartridge, printer_door, tester_panel, cart；对象：本branch物件/条件ID

前置：manufacturing inactive；CLEAN01 done

操作：按释放按钮取回未耗尽封闭料匣，放专属余料格；打印舱门关好，压板保持安全回撤，推回空运输车

后置：materials accounted；printer closed；tester safe idle；workspace reset

恢复：仍在加工的舱室不强开；保留等待状态直到安全释放

来源与设计：任务闭环复位是authored。具体抓握/运输/机构/按钮/离散状态为authored连接。未知：

### HAND_TOOL 取演示探针靠近、交互、退出

位置：WS_TEST；目标：blunt_probe, specimen, tool_rack；对象：本branch物件/条件ID

前置：R_TOOL_DEMO only；dedicated object；fixture-controlled pause；no real loaded-machine access without separate engineering safety design

操作：从架上拿mock软端探针，经侧面演示孔靠近格构；在场景指定接触点触发一次tool_contact事件，再退回并把探针放架上；演示继续记录鼓出状态；tool_contact不自动等于导致鼓出

后置：approach/contact/withdraw events recorded；demonstration tagged intervention；no pollution of quantitative unboxed curves

恢复：接触点/运动未知则只保留符号任务路径，不编造力幅；若真实测试禁入，保持guard关闭并使用专门远端工具接口

来源与设计：Video5约4.66–5.50s可见手持工具交互。具体抓握/运输/机构/按钮/离散状态为authored连接。未知：工具种类、作用目的、方向、力度、与曲线因果关系未知

## 附录B：77个来源单元的显式覆盖

纯非手工条目以N.记录覆盖，不用机械动作凑数。混合条目同时指向必要动手阶段和理论/分析。JSON提供完整操作模板列表；这里给可读分支/阶段定位。

|来源单元|定位|类别|对应操作/条件|非手工记录|
|---|---|---|---|---|
|main.intro|Abstract/introduction|nonmanual_only|无手工动作|N.A.mechanism, N.X.applications|
|main.buckling|Buckling of chiral and non-chiral rods|nonmanual_only|无手工动作|N.T.rod, N.T.oblique, N.T.linear, N.T.twist, N.T.geometry, N.T.thick|
|main.mechanism|Mechanism analysis|nonmanual_only|无手工动作|N.T.twist, N.T.phased, N.T.micropolar, N.A.mechanism|
|main.performance|Performance comparison|nonmanual_only|无手工动作|N.T.lattice, N.T.section, N.T.oblique|
|main.experiments|Experiments|mixed_hands_on_and_nonmanual|ASM01, ASM02, ASM03, ASM04, ASM05, FAB01, FAB02, FAB03, FAB04, POST_M, POST_R|N.P.design, N.A.rubber, N.A.tc4_cycles, N.A.tc4_match, N.A.layers, N.A.small|
|main.conclusions|Conclusions|nonmanual_only|无手工动作|N.A.mechanism, N.X.applications|
|methods.fea|Finite element analysis|nonmanual_only|无手工动作|N.I.models, N.T.tc4_match|
|methods.buckling|Bending buckling mode / compression buckling / parameter generalization|nonmanual_only|无手工动作|N.T.rod, N.T.oblique, N.T.thick|
|methods.chiral|Analytical model / stress evaluation|nonmanual_only|无手工动作|N.T.linear, N.T.twist|
|methods.metrics|Performance evaluation|mixed_hands_on_and_nonmanual|MET01, MET02|N.I.denominators, N.A.reduce, N.T.oblique, N.T.lattice|
|methods.samples|Samples|mixed_hands_on_and_nonmanual|R_SMALL20, R_SMALL50|N.I.design, N.I.material, N.P.design|
|methods.experiments|Experiments|mixed_hands_on_and_nonmanual|BND_BOX, BND_FREE, BND_LOCK, BND_OPEN, LOAD, OBS01, OBS_RESIDUAL, RELOAD, TEST02, TEST03, TEST04, UNLOAD|N.A.tc4_cycles, N.A.layers, N.I.acquisition, N.I.fixtures|
|methods.availability|Data/code availability|mixed_hands_on_and_nonmanual|LOAD, OBS01, OBS_RESIDUAL, RELOAD, TEST04, UNLOAD|N.I.models, N.I.acquisition|
|figure.Fig1|Fig1|mixed_hands_on_and_nonmanual|ASM01, ASM02, ASM03, ASM04, ASM05|N.T.rod, N.T.linear, N.T.twist, N.T.lattice, N.A.reduce|
|figure.Fig2|Fig2|nonmanual_only|无手工动作|N.T.rod, N.T.oblique, N.T.geometry, N.T.twist|
|figure.Fig3|Fig3|nonmanual_only|无手工动作|N.T.lattice, N.T.section, N.P.design|
|figure.Fig4|Fig4|mixed_hands_on_and_nonmanual|R01, R02, R03, R07, R08, R11, M12, M13, M14, M15, M16, R_SMALL20, R_SMALL50|N.A.rubber, N.A.tc4_cycles, N.A.reduce|
|figure.ED1|ED1|nonmanual_only|无手工动作|N.T.oblique, N.T.linear, N.T.twist|
|figure.ED2|ED2|nonmanual_only|无手工动作|N.T.rod, N.T.oblique|
|figure.ED3|ED3|nonmanual_only|无手工动作|N.T.geometry|
|figure.ED4|ED4|nonmanual_only|无手工动作|N.T.geometry, N.T.twist|
|figure.ED5|ED5|nonmanual_only|无手工动作|N.T.geometry, N.T.lattice|
|figure.ED6|ED6|nonmanual_only|无手工动作|N.T.thick|
|figure.ED7|ED7|nonmanual_only|无手工动作|N.T.phased|
|figure.ED8|ED8|nonmanual_only|无手工动作|N.T.lattice|
|figure.ED9|ED9|mixed_hands_on_and_nonmanual|R02, R03, R04, R05, R06, R07, R08, R09, R10, R11, R_PRISM_L1, R_PRISM_L2, R_PRISM_L4, R_PRISM_UNBOXED|N.A.layers|
|figure.ED10|ED10|mixed_hands_on_and_nonmanual|M12, M13, M14, M15, M16, M17, M_CHIRAL1, M_CHIRAL2, M_CHIRAL3, M_CHIRAL4|N.T.tc4_match, N.A.tc4_match|
|table.row1|Extended Data Table1 row1|mixed_hands_on_and_nonmanual|R01|N.A.reduce|
|table.row2|Extended Data Table1 row2|mixed_hands_on_and_nonmanual|R02|N.A.reduce|
|table.row3|Extended Data Table1 row3|mixed_hands_on_and_nonmanual|R03|N.A.reduce|
|table.row4|Extended Data Table1 row4|mixed_hands_on_and_nonmanual|R04|N.A.reduce|
|table.row5|Extended Data Table1 row5|mixed_hands_on_and_nonmanual|R05|N.A.reduce|
|table.row6|Extended Data Table1 row6|mixed_hands_on_and_nonmanual|R06|N.A.reduce|
|table.row7|Extended Data Table1 row7|mixed_hands_on_and_nonmanual|R07|N.A.reduce|
|table.row8|Extended Data Table1 row8|mixed_hands_on_and_nonmanual|R08|N.A.reduce|
|table.row9|Extended Data Table1 row9|mixed_hands_on_and_nonmanual|R09|N.A.reduce|
|table.row10|Extended Data Table1 row10|mixed_hands_on_and_nonmanual|R10|N.A.reduce|
|table.row11|Extended Data Table1 row11|mixed_hands_on_and_nonmanual|R11|N.A.reduce|
|table.row12|Extended Data Table1 row12|mixed_hands_on_and_nonmanual|M12|N.A.reduce|
|table.row13|Extended Data Table1 row13|mixed_hands_on_and_nonmanual|M13|N.A.reduce|
|table.row14|Extended Data Table1 row14|mixed_hands_on_and_nonmanual|M14|N.A.reduce|
|table.row15|Extended Data Table1 row15|mixed_hands_on_and_nonmanual|M15|N.A.reduce|
|table.row16|Extended Data Table1 row16|mixed_hands_on_and_nonmanual|M16|N.A.reduce|
|table.row17|Extended Data Table1 row17|mixed_hands_on_and_nonmanual|M17|N.A.reduce|
|si.variables|Supplementary Note variables List of variables|mixed_hands_on_and_nonmanual|MET01, MET02|N.T.rod, N.T.twist, N.I.denominators|
|si.1.1|Supplementary Note 1.1 Vertical rods|nonmanual_only|无手工动作|N.T.rod|
|si.1.2|Supplementary Note 1.2 Summary and analytical examples|nonmanual_only|无手工动作|N.T.rod|
|si.1.3|Supplementary Note 1.3 Oblique rods|nonmanual_only|无手工动作|N.T.oblique|
|si.1.4|Supplementary Note 1.4 Nonchiral lattice model|nonmanual_only|无手工动作|N.T.oblique|
|si.2|Supplementary Note 2 General3D chiral / linear model|nonmanual_only|无手工动作|N.T.linear|
|si.3.1|Supplementary Note 3.1 In-plane bending|nonmanual_only|无手工动作|N.T.twist|
|si.3.2|Supplementary Note 3.2 Out-of-plane bending|nonmanual_only|无手工动作|N.T.twist|
|si.3.3|Supplementary Note 3.3 In-rod twisting|nonmanual_only|无手工动作|N.T.twist|
|si.3.4|Supplementary Note 3.4 Helix correction|nonmanual_only|无手工动作|N.T.twist|
|si.3.5|Supplementary Note 3.5 Pure compression shortening|nonmanual_only|无手工动作|N.T.twist|
|si.3.6|Supplementary Note 3.6 Compatibility|nonmanual_only|无手工动作|N.T.twist|
|si.3.7.1|Supplementary Note 3.7.1 Force equilibrium|nonmanual_only|无手工动作|N.T.twist|
|si.3.7.2|Supplementary Note 3.7.2 Energy method|nonmanual_only|无手工动作|N.T.twist|
|si.3.8|Supplementary Note 3.8 Combined theory / iteration / stress|nonmanual_only|无手工动作|N.T.twist|
|si.4.1|Supplementary Note 4.1 Micropolar introduction|nonmanual_only|无手工动作|N.T.micropolar|
|si.4.2|Supplementary Note 4.2 Constitutive reduction|nonmanual_only|无手工动作|N.T.micropolar|
|si.4.3|Supplementary Note 4.3 Free rotation / two nonlinear models|nonmanual_only|无手工动作|N.T.micropolar|
|figure.S1|FigS1|nonmanual_only|无手工动作|N.T.rod|
|figure.S2|FigS2|nonmanual_only|无手工动作|N.T.oblique|
|figure.S3|FigS3|nonmanual_only|无手工动作|N.T.linear|
|figure.S4|FigS4|nonmanual_only|无手工动作|N.T.twist|
|figure.S5|FigS5|nonmanual_only|无手工动作|N.T.twist|
|figure.S6|FigS6|nonmanual_only|无手工动作|N.T.twist|
|figure.S7|FigS7|nonmanual_only|无手工动作|N.T.twist|
|figure.S8|FigS8|nonmanual_only|无手工动作|N.T.micropolar|
|video.1|Supplementary Video 1|nonmanual_only|无手工动作|N.T.section, N.T.rod|
|video.2|Supplementary Video 2|nonmanual_only|无手工动作|N.T.section, N.T.twist|
|video.3|Supplementary Video 3|nonmanual_only|无手工动作|N.T.section|
|video.4|Supplementary Video 4|hands_on_route|R01||
|video.5|Supplementary Video 5|mixed_hands_on_and_nonmanual|R_PRISM_L4, R_PRISM_UNBOXED, R_TOOL_DEMO|N.A.layers|
|video.6|Supplementary Video 6|hands_on_route|R03, R04||
|video.7|Supplementary Video 7|hands_on_route|R08, R09, R10, R11||


## 交付状态与边界

本稿为整篇范围的任务设计初版；来源单元均有处置，所有物理条件均有从材料到收尾的操作设计。操作接口尚未实施成完整机器人任务，整套场景/交互资产尚未全部搭完；已有静态粗级资产不等于可执行制造/装配机构。设计覆盖、场景资产、机器人可达/执行、科学复现是四个分开的轴。允许的下一步是根据此规范实现任务接口和评测；当前不启动物理仿真。
