# 热电器件：整篇论文驱动的长程移动操作任务族

> Public task-specification snapshot: source packets, scenes, models and runtime dependencies referenced below are not included. See ../../EXPORT_NOTES.md for current export boundaries. This is a design specification, not an executable or experimentally validated benchmark.

来源：[Composable neural emulators accelerate thermoelectric generator design](https://www.nature.com/articles/s41586-026-10223-1)，Nature 652，643–649（2026），DOI 10.1038/s41586-026-10223-1。

本轮重新阅读保留的主文12页和SI16页文本、全部图注与Methods，并复查主文PDF p4的Fig.3和SI PDF p13的Fig.21/22像素。来源定位、文件哈希和资产来源分开记录于provenance.json；没有逐点数字化所有图。首次草稿FIRST_ROUTE_PAIRED.md原样保留，不作为来源权威；本文件与配套JSON替代其未完成范围。

## 1. 这次交付的范围

从原料分装开始，包含三种材料路线、不同界面/烧结/切向、分段连接、单材料腿对照、双对模块、空间接触电阻和电流/热边界测量，以及恢复、归档与清理。来源inventory的7个分支全部有去向：6个有动手内容，1个纯计算族另行展开为12个非手工记录。

任务编排为15个配置、57个操作模板。6个制造配置对应三种粉末及三种烧结坯体；9个测量配置对应6个材料×长度功率比较、1个接触扫描、1个分段效率扫描、1个双对模块扫描。这不是15篇论文、15个原作者独立实验，也不是已运行15条机器人轨迹。

本阶段使用明确标记的惰性mock物料和预设科学读数。没有真实设备运行、热/电/粉末加工、机器人轨迹、物理仿真、TEGNet或COMSOL执行。现有参考资产保持不变。

## 2. 给agent的目标，不给完整参考答案

只向agent下发agent_visible.json中选中的一个episode：目标、原材料卡、初态、条件约束与公开接口。例：

> 从正确成分的封闭原料、空罐和空载工位开始，制备两对n–p热电模块，在指定热边界下取得带样品身份的mock电流、电压与冷侧热流记录。保留未知标定状态，保存物件与数据并复位工位。

初态不能放一个已经制好的模块让机器人直接测量。材料、空模具、未装载夹具和空测量腔体可以预置；加工输出只有在实体输入、正确工单及设备事件完成后才出现。

operations.json、branches.json、evaluator_reference.json与隐藏mock fixture属于评测侧。不能把完整工艺链、隐藏故障、源文9.3%/8.7%和4.0/4.9 μΩ cm²答案一起塞给agent。材料和条件卡可以包含来源报告的尺寸/温度/时长，属于任务约束；没有报告的值保留unknown或明确authored，不暗填为论文参数。

成功主要判断拿取、支撑、转移、对准、装卸、夹持、接线、条件切换、数据关联和收尾。等价且安全、保谱系的路径可接受；不是只有一串按钮顺序能得分。科学曲线可以预设，但按按钮本身不等于有效采集。

## 3. 场景与源事实的边界

WS_STOCK → WS_PREP/WS_ATMOSPHERE 或 WS_MELT → WS_MILL → WS_POWDER → WS_DIE/WS_SPS → WS_CUT → WS_JOIN 或 WS_MODULE → WS_CONTACT/WS_PEM → WS_DATA → WS_STORAGE/WS_CLEAN。

不同工位间必须插入MOVE：抓有号载具把手、跨工位移动、落入目的槽，不瞬移对象。微小腿可以有显式放大操纵代理，科学几何仍以毫米元数据保留；不能把放大比例当作论文样品尺寸。

原文支持材料、宏加工和测量类别。运输车、盖槽、模具键槽、夹具旋钮、冷态交接门、代理按钮、抓握姿态、气氛证书、稳定事件、恢复和清理微动作都是任务作者设计，不能说是原作者真实操作。

封闭服务仍保留实体操作：装正确输入，关闭外部交接接口，提交对象绑定工单，等处理完成，再等安全释放，打开允许的外部口，承托卸载同源输出。高温、压制、粉末动力学、抽真空和科学响应由mock事件代替。没有把“服务内部关闭”宣称成“全部人工微动作已复刻”；granularity_gaps.json逐段列出缺口。

## 4. 三种制造路线不能互换

### 4.1 P：MgAgSb不是无添加纯材料

Methods中的全称为MgAgSb + 0.625 wt% C18H36O2。添加物的具体异构体、纯度和加料时序未报告，不根据化学式自动补名称。Mg、Ag、Sb原料与添加物均保持独立批次，再合成粉末子谱系。[Materials synthesis，主文PDF p8](https://www.nature.com/articles/s41586-026-10223-1.pdf#page=8)

STOCK/PREP_NEST/PORTION：分别打开原料瓶，用模拟勺转至带号盘/罐，逐瓶关盖归位。来源没有真实批质量、球料比和称量公差；mock份额由任务manifest明确分配。不是把未知份额写成可实做配方。

VIAL_CLOSE/AR_HANDOFF/AR_RETURN：合罐置交接盒，把盒装Ar代理外侧抽屉、关门，等可信封存状态再领回。论文报告Ar中球磨5 h；普通盖罐外观不证明气密，也不证明Ar状态。气氛状态由环境事件给出，不能让agent自行改成true。

MILL_OPEN/SEAT/CLAMP/CLOSE/RUN/UNLOAD：开锁扣抬罩、承托罐放入任务夹座、转夹紧代理、退出并关罩、选择本批5 h工单。结束后必须停机和释放，先承托再松夹取罐。出粉在封闭代理区执行开盖、转移、分装和封盖，留下余料账本。

### 4.2 N：简称中隐藏In与Te

主文简称Mg3Bi1.4Sb0.6实际对应Mg3.2In0.02Sb0.595Bi1.4Te0.005。不能在原料、粉末或最终模块谱系中删除In/Te、Mg过量或Sb分数。N也走Ar球磨5 h，但粉末、罐和工单与P不同。作者贡献说明N材料由合作作者提供，不能把本任务统一操作台当成原作者同一人原位制造的证据。[主文PDF pp8–9](https://www.nature.com/articles/s41586-026-10223-1.pdf#page=8)

### 4.3 B：Bi0.4Sb1.6Te3先熔锭，后球磨

B的Bi/Sb/Te先分装到盘，装进石英管的V槽托架，交接封装代理。TUBE_LOAD/MELT_LOAD/RUN/UNLOAD明确包含拿管、装料、冷态上料、关门、等待完成与冷却、取架、通过开管代理取得同号锭，再放入B专用球磨罐。来源为1273 K熔制12 h，随后锭球磨1 h。[Materials synthesis，主文PDF p8](https://www.nature.com/articles/s41586-026-10223-1.pdf#page=8)

石英管尺寸、密封法、炉型、气氛、冷却以及真实开管/取锭动作未知。不擅加真空封管、淬火、破碎，也不把P/N的Ar气氛无条件继承给B。B不能跳过熔锭直接复用P/N的5 h球磨路线。

## 5. 装模、烧结、切向和子样

DIE_ASSEMBLE：装下冲和模套代理，给压制轴建立不可丢失的方向标识。P_STACK逐层放Sb、P和Sb；B_STACK只装B、不加界面料。N使用不锈钢界面粉末；任务以两端代理层实现，具体端层几何和厚度并非来源复原。

DIE_CLOSE/SPS_LOAD/RUN/UNLOAD/DEMOLD：插上冲、限位托盘、装正确设备外侧接口、关门启动、等工艺及冷态释放、取盘，回脱模槽逐件撤冲/模套并承托坯体。原文条件：

- P：SPS-322LX，573 K，5 min，60 MPa，Sb界面
- B：SPS-322LX，693 K，10 min，60 MPa，无界面材料
- N：SPS-1080 System，973 K，10 min，60 MPa，不锈钢界面

这些是来源工单标签，不是已经批准的真实设备SOP。模具材质/几何、内衬、升降温、压力轨迹和脱模力仍未知。[TE generator fabrication，主文PDF p8](https://www.nature.com/articles/s41586-026-10223-1.pdf#page=8)

CUT_FIXTURE/SELECT/RUN/UNLOAD：拿方向座、安放坯体、对准方向、两侧支撑、选尺寸、撤手关罩、启动封闭切割、停止释放后逐腿分格。P的Sb/P/Sb件平行压制方向切，B垂直；N切向未报告，不能套P规则。原文“cut parallel/perpendicular”的局部切面/长轴工程解释未完整给出，任务夹具实现单独标authored。

切割输出有独立子ID、父坯体与原位置、方向、尺寸来源、余料和破损状态。制造四腿时要有两条不同P和两条不同N；不能把一个ID放四个槽。真实产率/质量未知，mock只做明确份额和数量账本。

## 6. 分段、单腿和双对模块各自成路线

### 6.1 分段连接有两类界面

GA_SETUP把P和B分别装对合夹具，选P的Sb端朝B裸端。GA_APPLY取有号Ga–In惰性涂布代理，在相接面转移模拟层，归还工具。SEG_JOIN对准共同轴线合拢、限位，稳定后连承托取出。

最终结构是Sb/P/Sb/Ga–In/B；MgAgSb/Bi0.4Sb1.6Te3只是简称。Ga–In不是Sb界面的替代，也不是双对Cu电极的已知焊料。用量、Ga/In比例、润湿/压力/停留和真实表面处理未报告，禁止写成作者采用的工艺。[主文PDF p8](https://www.nature.com/articles/s41586-026-10223-1.pdf#page=8)

源文选择P长度占总长度0.5。接口厚度及报告总长是否包括界面未澄清，不能用额外“40 μm”把源长拆成精确核心长度。任务在分段phase单独绑定组件尺寸：6.7/8.8 mm成品各用两半长代理组件，8 mm未知源几何任务用4+4 mm；接口在mock里是包络内逻辑面、不额外加长。这是实现0.5比例和总长约束的任务分配，不是已知的真实核心厚度。

### 6.2 六个实验功率密度比较配置

Fig.3i中B单腿、P/B分段腿、P单腿各有总长6.7与8.8 mm，共六个配置。它们的实验横截面和该图具体热边界没有独立给出。Fig.3d/e的a=b=3.5 mm、c=7/8/9/10 mm是计算，不得移植为这些实物几何。[Fig.3，主文PDF p4](https://www.nature.com/articles/s41586-026-10223-1.pdf#page=4)

为让任务夹持和对照可执行，六个mock配置使用明确authored的4×4 mm截面及Th=473 K/Tc=293 K匹配条件；这不声称还原Fig.3i原始边界。源长6.7/8.8 mm保留。单材料控制的端接/制样细节未分别说明，本任务复用相应组件制造前缀，但标为任务复用，不将其升格为原作者单腿SOP。

### 6.3 分段效率与接触扫描不偷用尺寸

Fig.3j效率扫描有Th=373、473、573、593 K，Tc=293 K。该面板样品尺寸及它与Fig.3i样品是否复用未知。CONTACT_SEG和EFFICIENCY_SEG使用明确authored的4×4×8 mm代理与独立兄弟谱系，不把两个面板硬拼为同一个已验证样品。接触扫描图的横坐标也不当作完整几何测量。

### 6.4 双对模块保留P/N尺寸差

P两腿分别3.3×3.3×6.6 mm，N两腿分别2.9×2.9×6.6 mm。不能用相同腿复制缩放成“差不多的双对”。MODULE_BASE拿AlN板、放底铜片与端子；MODULE_LEGS逐腿放P1/N1/P2/N2；MODULE_BRIDGE对上铜桥并用惰性代理连接；MODULE_RELEASE承托板、撤临时定位件、取入运输架。[主文PDF pp5–6、8](https://www.nature.com/articles/s41586-026-10223-1.pdf#page=6)

来源说AlN板和铜电极，架构电串联/热并联；精确铜片拓扑、板厚、接合法、热接触材料与装配载荷未知。现有网格的10×10×0.8 mm AlN、40 μm端皮和铜拓扑是基准设计时的资产假设，不是论文加工尺寸。模块拆解显示控件不能当真实可重复无损拆焊。

## 7. S1331：真实任务是沿位置取得电阻

CONTACT_MOUNT把完整分段样横放座内、夹持，登记B→Ga–In/Sb→P的空间方向及原点，停源状态接任务引线。CONTACT_PROBE将探针移到首点并落到公开接触反馈。CONTACT_SCAN每个点都采集x、R、单位、样品和运行号，抬针、移动、再落针，跨界面保持顺序。结束停源、撤针、断线，承托解夹取样。[Fig.3h主文PDF p4；SI Fig.21 PDF p13](https://media.springernature.com/original/springer-static/esm/art%3A10.1038%2Fs41586-026-10223-1/MediaObjects/41586_2026_10223_MOESM1_ESM.pdf#page=13)

实际探针数量/电路、接触力、电流、间距、位置步长、标定和拟合细节未知；JSON里的0–8 mm整数格只是mock坐标。不能凭一张装置照片补一个四探针SOP。

Sb/P和B/Ga–In/Sb是同件内不同界面。来源接触电阻率4.0与4.9 μΩ cm²是参考事实，不是仪器直接返回的两个按钮值。原始是R(x)；派生电阻率需要界面电阻处理方法和面积。缺面积/标定则保存曲线、标unknown，不拿论文数值填满结果。

## 8. Mini-PEM：装载、真空、热边界、逐点采集

PEM_PREP在空载、停源、冷态且安全放气后开腔，装对应腿/模块底托。PEM_MOUNT承托样品放下接触，上接触下降到任务就绪。分段样的P/MgAgSb端在上热侧，B端在下冷侧，与SI21照片一致。真实载荷和热界面材料未知。

PEM_WIRE逐根连有号端口并理线，核对极性/通道/标定。PEM_SEAL关腔、退出，启动mock真空，等环境给vacuum_ready。PEM_BOUNDARY选择条件并等稳定，不能自行填真空/稳定成功。来源测量下端293 K，上端373–593 K；Fig.3j和Fig.4h/i明确显示373、473、573、593 K四条件。[TE generator measurement主文PDF p8](https://www.nature.com/articles/s41586-026-10223-1.pdf#page=8)

每个热边界内，PEM_CURRENT选一个任务电流点、等点就绪，再PEM_ACQUIRE采集实际mock I/V/Qc（或原始热流传感电压）。遍历电流点后再切热边界并重新稳定。源电流格点/停留判据未给出，不能直接把图坐标刻度当全部实验步长。更换边界仍是同一个物件和新condition ID，不成为新的独立制造n。

结束PEM_POWERDOWN停输出/加热并冷却，PEM_OPEN等可信冷态、放气、安全开门，再PEM_UNLOAD断线、托样、松上接触、取样、卸底托并关空腔。到时间不等于可触碰，不得因为mock程序完成就省略释放。

## 9. 计算是数据处理，不再造手动作

P=I×V；η=P/(P+Qc)。I用A、V用mV得到mW；和Qc合算效率前必须统一单位。P/面积只有登记真实来源或明确mock截面时才有效；不能把模块外部板面积当腿截面积。每个条件取采样点的Pmax/ηmax，未拟合时不声称找到了连续曲线精确极值。

热流单位要特别留真：Fig.2a把Q0标mV，Fig.2b标W，Methods称冷侧热流，这是未解决的源图标签不一致。Fig.2属于计算，不因此证明Mini-PEM输出某个mV传感信号。任务若提供raw mV热流通道且无标定，保留原始信号，η未知；只有明确标定的mock Qc[W]才支持mock效率。两类样例在mock_contract.json分开，不静默将mV改W。

9.3%分段效率、8.7%双对效率、4.0/4.9 μΩ cm²接触电阻率都不作为机械操作数值奖励。没有有效采集事件的“正确数字”不及格；有效采集后结果未知或较差不自动算操作失败。

## 10. 全部纯计算与文献内容的处置

nonmanual_scope.json保留模型数据/训练、材料泛化、域外与新材料、分段几何、恒热流、电/热接触寄生、n–p几何、对数扩展、复杂组合与文献比较12类。覆盖主文Fig.1–4的计算部分、ED1–3、SI1–20和22–26；SI21单独属于实际测量装置。

- 1/2/4/8/16/32对扩展是SI22计算，只有双对模块的实际制造被报道
- Mg3Sb1.5Bi0.5–SnS、分段n腿与GeTe、三段与分段p腿、全部材料组合都不变成新增实物
- ED3热接触电阻率扫描不生成一台未报道的实验测热阻仪
- zT/PF曲线不让任务凭空增加Seebeck/XRD/热导率实测流程
- 文献器件/材料性质是参照，不能生成“本篇新做的对照”样品
- 计算中将n/p电压转换为正值的约定，不能成为篡改实测极性的许可

## 11. 恢复和清理也是动作

错料投前可关盖退回重取；投后混料隔离另起批，不删除父料。夹持不牢先停机/释放、承托再重装。错切向已切成件不可通过旋转标签恢复，必须隔离重制。错接Ga–In层、破腿或已粘结未知损伤不以显示分离当无损修复。

接触丢点记录无效，停源抬针后重定位、另建重测事件。热漂移打断当前采集，保留同物件历史、重新稳定后新attempt。缺标定照样保存raw，不将参考图点当补值。释放状态不来就保持封闭并报告阻塞。

ARCHIVE把未用、已测、探针接触、破损和未知分格，封余粉/腿/边料并核数量。CLEAN逐件归还模套、冲头、限位件、模拟勺、载具和线；粉末、金属、石英管代理废物分别封盒交接，擦允许表面后收擦片，留下空载关闭工位。没有吹散粉末、扫裸碎管或临时配化学清洗液。

## 12. 已有资产与尚缺接口

asset_bindings.json逐操作绑定66类资产角色。已存在SPEX8000D与双对模块网格，重用确实存在的part ID；其他角色只是任务资产需求，不声明已建成。

SPEX工作站结论仍为LIMITED：罐与夹具存在约7 mm AABB间隙、罩壳接触未解、气密/夹紧/连续运动/机器人可达性未验证。现有开盖/提罐/按键是静态显示。若动态任务使用新mock定位座，必须标authored并单独实现，不能用当前图像宣布抓取装载已经成立。

文件入口：agent_visible.json用于单episode目标；operations.json与branches.json用于参考动作与分支；material_cards.json、lineage_contract.json和control_packages.json维持身份与对照；mock_contract.json和evaluator_reference.json限定读数与验收；asset_bindings.json、unknown_parameters.json与granularity_gaps.json记录实现需要；coverage_matrix.json和provenance.json审计整篇范围。

本包达到“整篇任务设计与来源分流就绪”，不是“现实实验/机器人执行/全部人工微动作复刻就绪”。下一步应实现选定episode的外部操作接口并做轨迹验证；本轮不把这份设计自动升格为已运行资产或已复现科学结果。
