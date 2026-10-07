Attribute VB_Name = "AutoFullArmStaticV3"
Option Explicit
' STAGED SOURCE ONLY: not compiled or executed in SOLIDWORKS.
' Requires SOLIDWORKS type library AND SOLIDWORKS constants type library.
' Upload this source and all 28 STEP files FLAT in the same directory.
' Save its .swp in that directory before running main.
' Produces native static home-pose geometry, not mates/motion/FEA.
' Source matrices: column-vector world_from_link_home, translation mm.
' SW MathTransform: transposed rotation storage, translation m, scale 1.
' Source inputs and any existing output files are never overwritten.
' No shell/network calls or account operations.

Private swApp As SldWorks.SldWorks
Private mathUtil As SldWorks.MathUtility
Private runtimeLog As String
Private logReady As Boolean
Private oldMapping As Long, oldUnits As Long
Private oldInterconnect As Boolean, oldSolidSurface As Boolean, oldDiagnostics As Boolean
Private prefsCaptured As Boolean
Private linkNames(0 To 27) As String
Private expectedCounts(0 To 27) As Long
Private homeData(0 To 27) As Variant
Private expectedPoints(0 To 27) As Variant
Private nativePaths(0 To 27) As String
Private importedModels(0 To 27) As SldWorks.ModelDoc2
Private components(0 To 27) As SldWorks.Component2

Private Sub LogLine(ByVal message As String)
    Dim channel As Integer, entry As String
    entry = Format$(Now, "yyyy-mm-dd hh:nn:ss") & " | " & message
    Debug.Print entry
    If logReady Then
        channel = FreeFile
        Open runtimeLog For Append As #channel
        Print #channel, entry
        Close #channel
    End If
End Sub

Private Sub Check(ByVal condition As Boolean, ByVal message As String)
    If condition = False Then Err.Raise vbObjectError + 720, "AutoFullArmStaticV3", message
End Sub

Private Function CountArray(ByVal items As Variant) As Long
    If IsEmpty(items) Then
        CountArray = 0
    ElseIf IsArray(items) Then
        CountArray = UBound(items) - LBound(items) + 1
    Else
        Err.Raise vbObjectError + 721, "CountArray", "Expected an array or Empty"
    End If
End Function

Private Sub InitData()
    linkNames(0) = "base_link"
    expectedCounts(0) = 1
    homeData(0) = Array(1#, 0#, 0#, 0#, -1#, 0#, 0#, 0#, -1#, 0#, 0#, 1.0800000000000001#, 1#, 0#, 0#, 0#)
    expectedPoints(0) = Array(0#, 0#, 1.0800000000000001#, 0.01#, 0#, 1.0800000000000001#, 0#, -0.01#, 1.0800000000000001#, 0#, 0#, 1.0700000000000001#)
    linkNames(1) = "shoulder_abduction"
    expectedCounts(1) = 5
    homeData(1) = Array(1#, 0#, 0#, 0#, -0.99500416527802593#, -0.099833416646828044#, 0#, 0.099833416646828044#, -0.99500416527802593#, 0#, 0#, 1.0800000000000001#, 1#, 0#, 0#, 0#)
    expectedPoints(1) = Array(0#, 0#, 1.0800000000000001#, 0.01#, 0#, 1.0800000000000001#, 0#, -0.0099500416527802584#, 1.0790016658335317#, 0#, 0.00099833416646828038#, 1.0700499583472198#)
    linkNames(2) = "shoulder_flexion"
    expectedCounts(2) = 1
    homeData(2) = Array(0.96891242171064473#, -0.024699182544331663#, 0.24616796996452536#, 0#, -0.99500416527802615#, -0.099833416646828058#, 0.24740395925452299#, 0.096729837490925966#, -0.9640718953917109#, 0#, 0#, 1.0800000000000001#, 1#, 0#, 0#, 0#)
    expectedPoints(2) = Array(0#, 0#, 1.0800000000000001#, 0.0096891242171064478#, -0.00024699182544331663#, 1.0824616796996454#, 0#, -0.0099500416527802601#, 1.0790016658335317#, 0.0024740395925452303#, 0.00096729837490925968#, 1.0703592810460829#)
    linkNames(3) = "upper_arm"
    expectedCounts(3) = 13
    homeData(3) = Array(0.96891242171064473#, -0.024699182544331663#, 0.24616796996452536#, 0#, -0.99500416527802615#, -0.099833416646828058#, 0.24740395925452299#, 0.096729837490925966#, -0.9640718953917109#, 0#, 0#, 1.0800000000000001#, 1#, 0#, 0#, 0#)
    expectedPoints(3) = Array(0#, 0#, 1.0800000000000001#, 0.0096891242171064478#, -0.00024699182544331663#, 1.0824616796996454#, 0#, -0.0099500416527802601#, 1.0790016658335317#, 0.0024740395925452303#, 0.00096729837490925968#, 1.0703592810460829#)
    linkNames(4) = "elbow_link"
    expectedCounts(4) = 11
    homeData(4) = Array(0.21900668709304127#, -0.097409796513950958#, 0.97084880519658745#, 0#, -0.99500416527802615#, -0.099833416646828058#, 0.9757233578266592#, 0.02186418584100111#, -0.21791256588131769#, 0.074221187776356903#, 0.02901895124727779#, 0.79077843138248682#, 1#, 0#, 0#, 0#)
    expectedPoints(4) = Array(0.074221187776356903#, 0.02901895124727779#, 0.79077843138248682#, 0.076411254647287319#, 0.02804485328213828#, 0.80048691943445272#, 0.074221187776356903#, 0.01906890959449753#, 0.7897800972160185#, 0.083978421354623495#, 0.029237593105687801#, 0.78859930572367365#)
    linkNames(5) = "forearm"
    expectedCounts(5) = 69
    homeData(5) = Array(0.21900668709304127#, -0.097409796513950958#, 0.97084880519658745#, 0#, -0.99500416527802615#, -0.099833416646828058#, 0.9757233578266592#, 0.02186418584100111#, -0.21791256588131769#, 0.074221187776356903#, 0.02901895124727779#, 0.79077843138248682#, 1#, 0#, 0#, 0#)
    expectedPoints(5) = Array(0.074221187776356903#, 0.02901895124727779#, 0.79077843138248682#, 0.076411254647287319#, 0.02804485328213828#, 0.80048691943445272#, 0.074221187776356903#, 0.01906890959449753#, 0.7897800972160185#, 0.083978421354623495#, 0.029237593105687801#, 0.78859930572367365#)
    linkNames(6) = "wrist_pitch"
    expectedCounts(6) = 4
    homeData(6) = Array(0.020794827803092053#, -0.099811829087050177#, 0.99478900974575379#, 0#, -0.99500416527802615#, -0.099833416646828071#, 0.9997837641893571#, 0.0020760187081651643#, -0.02069094028031615#, 0.31815202723302172#, 0.034484997707528067#, 0.73630028991215735#, 1#, 0#, 0#, 0#)
    expectedPoints(6) = Array(0.31815202723302172#, 0.034484997707528067#, 0.73630028991215735#, 0.31835997551105266#, 0.033486879416657567#, 0.7462481800096149#, 0.31815202723302172#, 0.024534956054747807#, 0.73530195574568902#, 0.32814986487491526#, 0.034505757894609718#, 0.73609338050935413#)
    linkNames(7) = "palm_base"
    expectedCounts(7) = 13
    homeData(7) = Array(0.020794827803092053#, -0.099811829087050177#, 0.99478900974575379#, 0#, -0.99500416527802615#, -0.099833416646828071#, 0.9997837641893571#, 0.0020760187081651643#, -0.02069094028031615#, 0.35814337780059602#, 0.034568038455854676#, 0.73547265230094483#, 1#, 0#, 0#, 0#)
    expectedPoints(7) = Array(0.35814337780059602#, 0.034568038455854676#, 0.73547265230094483#, 0.35835132607862696#, 0.033569920164984175#, 0.74542054239840239#, 0.35814337780059602#, 0.024617996803074416#, 0.7344743181344765#, 0.36814121544248957#, 0.034588798642936326#, 0.73526574289814162#)
    linkNames(8) = "index_knuckle"
    expectedCounts(8) = 1
    homeData(8) = Array(0.020794827803092053#, -0.099811829087050177#, 0.99478900974575379#, 0#, -0.99500416527802615#, -0.099833416646828071#, 0.9997837641893571#, 0.0020760187081651643#, -0.02069094028031615#, 0.45812175421953166#, 0.0049255153683304157#, 0.73040855577350827#, 1#, 0#, 0#, 0#)
    expectedPoints(8) = Array(0.45812175421953166#, 0.0049255153683304157#, 0.73040855577350827#, 0.45832970249756261#, 0.0039273970774599144#, 0.74035644587096583#, 0.45812175421953166#, -0.0050245262844498444#, 0.72941022160703994#, 0.46811959186142521#, 0.004946275555412067#, 0.73020164637070506#)
    linkNames(9) = "index_proximal"
    expectedCounts(9) = 12
    homeData(9) = Array(0.020794827803092053#, -0.099811829087050177#, 0.99478900974575379#, 0#, -0.99500416527802615#, -0.099833416646828071#, 0.9997837641893571#, 0.0020760187081651643#, -0.02069094028031615#, 0.45812175421953166#, 0.0049255153683304157#, 0.73040855577350827#, 1#, 0#, 0#, 0#)
    expectedPoints(9) = Array(0.45812175421953166#, 0.0049255153683304157#, 0.73040855577350827#, 0.45832970249756261#, 0.0039273970774599144#, 0.74035644587096583#, 0.45812175421953166#, -0.0050245262844498444#, 0.72941022160703994#, 0.46811959186142521#, 0.004946275555412067#, 0.73020164637070506#)
    linkNames(10) = "index_intermediate"
    expectedCounts(10) = 12
    homeData(10) = Array(0.020794827803092053#, -0.099811829087050177#, 0.99478900974575379#, 0#, -0.99500416527802615#, -0.099833416646828071#, 0.9997837641893571#, 0.0020760187081651643#, -0.02069094028031615#, 0.49811310478710596#, 0.0050085561166570225#, 0.72958091816229564#, 1#, 0#, 0#, 0#)
    expectedPoints(10) = Array(0.49811310478710596#, 0.0050085561166570225#, 0.72958091816229564#, 0.49832105306513691#, 0.0040104378257865211#, 0.7395288082597532#, 0.49811310478710596#, -0.0049414855361232376#, 0.72858258399582732#, 0.50811094242899957#, 0.0050293163037386738#, 0.72937400875949243#)
    linkNames(11) = "index_distal"
    expectedCounts(11) = 10
    homeData(11) = Array(0.020794827803092053#, -0.099811829087050177#, 0.99478900974575379#, 0#, -0.99500416527802615#, -0.099833416646828071#, 0.9997837641893571#, 0.0020760187081651643#, -0.02069094028031615#, 0.52210791512765042#, 0.0050583805656529866#, 0.72908433559556807#, 1#, 0#, 0#, 0#)
    expectedPoints(11) = Array(0.52210791512765042#, 0.0050583805656529866#, 0.72908433559556807#, 0.52231586340568137#, 0.0040602622747824852#, 0.73903222569302562#, 0.52210791512765042#, -0.0048916610871272736#, 0.72808600142909974#, 0.53210575276954397#, 0.0050791407527346379#, 0.72887742619276485#)
    linkNames(12) = "middle_knuckle"
    expectedCounts(12) = 1
    homeData(12) = Array(0.020794827803092053#, -0.099811829087050177#, 0.99478900974575379#, 0#, -0.99500416527802615#, -0.099833416646828071#, 0.9997837641893571#, 0.0020760187081651643#, -0.02069094028031615#, 0.45812175421953166#, 0.024825598673890933#, 0.73240522410644482#, 1#, 0#, 0#, 0#)
    expectedPoints(12) = Array(0.45812175421953166#, 0.024825598673890933#, 0.73240522410644482#, 0.45832970249756261#, 0.023827480383020433#, 0.74235311420390238#, 0.45812175421953166#, 0.014875557021110673#, 0.73140688993997649#, 0.46811959186142521#, 0.024846358860972584#, 0.73219831470364161#)
    linkNames(13) = "middle_proximal"
    expectedCounts(13) = 12
    homeData(13) = Array(0.020794827803092053#, -0.099811829087050177#, 0.99478900974575379#, 0#, -0.99500416527802615#, -0.099833416646828071#, 0.9997837641893571#, 0.0020760187081651643#, -0.02069094028031615#, 0.45812175421953166#, 0.024825598673890933#, 0.73240522410644482#, 1#, 0#, 0#, 0#)
    expectedPoints(13) = Array(0.45812175421953166#, 0.024825598673890933#, 0.73240522410644482#, 0.45832970249756261#, 0.023827480383020433#, 0.74235311420390238#, 0.45812175421953166#, 0.014875557021110673#, 0.73140688993997649#, 0.46811959186142521#, 0.024846358860972584#, 0.73219831470364161#)
    linkNames(14) = "middle_intermediate"
    expectedCounts(14) = 12
    homeData(14) = Array(0.020794827803092053#, -0.099811829087050177#, 0.99478900974575379#, 0#, -0.99500416527802615#, -0.099833416646828071#, 0.9997837641893571#, 0.0020760187081651643#, -0.02069094028031615#, 0.50311202360805274#, 0.024919019515758364#, 0.7314741317938307#, 1#, 0#, 0#, 0#)
    expectedPoints(14) = Array(0.50311202360805274#, 0.024919019515758364#, 0.7314741317938307#, 0.50331997188608368#, 0.023920901224887863#, 0.74142202189128825#, 0.50311202360805274#, 0.014968977862978104#, 0.73047579762736237#, 0.51310986124994629#, 0.024939779702840014#, 0.73126722239102748#)
    linkNames(15) = "middle_distal"
    expectedCounts(15) = 10
    homeData(15) = Array(0.020794827803092053#, -0.099811829087050177#, 0.99478900974575379#, 0#, -0.99500416527802615#, -0.099833416646828071#, 0.9997837641893571#, 0.0020760187081651643#, -0.02069094028031615#, 0.52810661771278666#, 0.024970919983462493#, 0.73095685828682277#, 1#, 0#, 0#, 0#)
    expectedPoints(15) = Array(0.52810661771278666#, 0.024970919983462493#, 0.73095685828682277#, 0.52831456599081761#, 0.023972801692591993#, 0.74090474838428033#, 0.52810661771278666#, 0.015020878330682233#, 0.72995852412035445#, 0.53810445535468021#, 0.024991680170544144#, 0.73074994888401956#)
    linkNames(16) = "ring_knuckle"
    expectedCounts(16) = 1
    homeData(16) = Array(0.020794827803092053#, -0.099811829087050177#, 0.99478900974575379#, 0#, -0.99500416527802615#, -0.099833416646828071#, 0.9997837641893571#, 0.0020760187081651643#, -0.02069094028031615#, 0.45812175421953166#, 0.044725681979451454#, 0.73440189243938137#, 1#, 0#, 0#, 0#)
    expectedPoints(16) = Array(0.45812175421953166#, 0.044725681979451454#, 0.73440189243938137#, 0.45832970249756261#, 0.043727563688580953#, 0.74434978253683892#, 0.45812175421953166#, 0.034775640326671194#, 0.73340355827291304#, 0.46811959186142521#, 0.044746442166533104#, 0.73419498303657815#)
    linkNames(17) = "ring_proximal"
    expectedCounts(17) = 12
    homeData(17) = Array(0.020794827803092053#, -0.099811829087050177#, 0.99478900974575379#, 0#, -0.99500416527802615#, -0.099833416646828071#, 0.9997837641893571#, 0.0020760187081651643#, -0.02069094028031615#, 0.45812175421953166#, 0.044725681979451454#, 0.73440189243938137#, 1#, 0#, 0#, 0#)
    expectedPoints(17) = Array(0.45812175421953166#, 0.044725681979451454#, 0.73440189243938137#, 0.45832970249756261#, 0.043727563688580953#, 0.74434978253683892#, 0.45812175421953166#, 0.034775640326671194#, 0.73340355827291304#, 0.46811959186142521#, 0.044746442166533104#, 0.73419498303657815#)
    linkNames(18) = "ring_intermediate"
    expectedCounts(18) = 12
    homeData(18) = Array(0.020794827803092053#, -0.099811829087050177#, 0.99478900974575379#, 0#, -0.99500416527802615#, -0.099833416646828071#, 0.9997837641893571#, 0.0020760187081651643#, -0.02069094028031615#, 0.49811310478710596#, 0.044808722727778062#, 0.73357425482816885#, 1#, 0#, 0#, 0#)
    expectedPoints(18) = Array(0.49811310478710596#, 0.044808722727778062#, 0.73357425482816885#, 0.49832105306513691#, 0.043810604436907562#, 0.7435221449256264#, 0.49811310478710596#, 0.034858681074997802#, 0.73257592066170052#, 0.50811094242899957#, 0.044829482914859713#, 0.73336734542536564#)
    linkNames(19) = "ring_distal"
    expectedCounts(19) = 10
    homeData(19) = Array(0.020794827803092053#, -0.099811829087050177#, 0.99478900974575379#, 0#, -0.99500416527802615#, -0.099833416646828071#, 0.9997837641893571#, 0.0020760187081651643#, -0.02069094028031615#, 0.52210791512765042#, 0.044858547176774025#, 0.73307767226144116#, 1#, 0#, 0#, 0#)
    expectedPoints(19) = Array(0.52210791512765042#, 0.044858547176774025#, 0.73307767226144116#, 0.52231586340568137#, 0.043860428885903524#, 0.74302556235889872#, 0.52210791512765042#, 0.034908505523993764#, 0.73207933809497283#, 0.53210575276954397#, 0.044879307363855675#, 0.73287076285863795#)
    linkNames(20) = "pinky_knuckle"
    expectedCounts(20) = 1
    homeData(20) = Array(0.020794827803092053#, -0.099811829087050177#, 0.99478900974575379#, 0#, -0.99500416527802615#, -0.099833416646828071#, 0.9997837641893571#, 0.0020760187081651643#, -0.02069094028031615#, 0.45312283539858494#, 0.064615385191471142#, 0.73650201547371952#, 1#, 0#, 0#, 0#)
    expectedPoints(20) = Array(0.45312283539858494#, 0.064615385191471142#, 0.73650201547371952#, 0.45333078367661589#, 0.063617266900600641#, 0.74644990557117707#, 0.45312283539858494#, 0.054665343538690882#, 0.73550368130725119#, 0.46312067304047849#, 0.064636145378552792#, 0.73629510607091631#)
    linkNames(21) = "pinky_proximal"
    expectedCounts(21) = 12
    homeData(21) = Array(0.020794827803092053#, -0.099811829087050177#, 0.99478900974575379#, 0#, -0.99500416527802615#, -0.099833416646828071#, 0.9997837641893571#, 0.0020760187081651643#, -0.02069094028031615#, 0.45312283539858494#, 0.064615385191471142#, 0.73650201547371952#, 1#, 0#, 0#, 0#)
    expectedPoints(21) = Array(0.45312283539858494#, 0.064615385191471142#, 0.73650201547371952#, 0.45333078367661589#, 0.063617266900600641#, 0.74644990557117707#, 0.45312283539858494#, 0.054665343538690882#, 0.73550368130725119#, 0.46312067304047849#, 0.064636145378552792#, 0.73629510607091631#)
    linkNames(22) = "pinky_intermediate"
    expectedCounts(22) = 12
    homeData(22) = Array(0.020794827803092053#, -0.099811829087050177#, 0.99478900974575379#, 0#, -0.99500416527802615#, -0.099833416646828071#, 0.9997837641893571#, 0.0020760187081651643#, -0.02069094028031615#, 0.48611569961683371#, 0.064683893808840598#, 0.73581921444446918#, 1#, 0#, 0#, 0#)
    expectedPoints(22) = Array(0.48611569961683371#, 0.064683893808840598#, 0.73581921444446918#, 0.48632364789486465#, 0.063685775517970097#, 0.74576710454192674#, 0.48611569961683371#, 0.054733852156060338#, 0.73482088027800085#, 0.49611353725872726#, 0.064704653995922248#, 0.73561230504166597#)
    linkNames(23) = "pinky_distal"
    expectedCounts(23) = 10
    homeData(23) = Array(0.020794827803092053#, -0.099811829087050177#, 0.99478900974575379#, 0#, -0.99500416527802615#, -0.099833416646828071#, 0.9997837641893571#, 0.0020760187081651643#, -0.02069094028031615#, 0.50611137490062086#, 0.064725414183003899#, 0.73540539563886287#, 1#, 0#, 0#, 0#)
    expectedPoints(23) = Array(0.50611137490062086#, 0.064725414183003899#, 0.73540539563886287#, 0.5063193231786518#, 0.063727295892133398#, 0.74535328573632043#, 0.50611137490062086#, 0.054775372530223639#, 0.73440706147239454#, 0.51610921254251441#, 0.064746174370085549#, 0.73519848623605966#)
    linkNames(24) = "thumb_opposition"
    expectedCounts(24) = 2
    homeData(24) = Array(0.020794827803092053#, -0.099811829087050177#, 0.99478900974575379#, 0#, -0.99500416527802615#, -0.099833416646828071#, 0.9997837641893571#, 0.0020760187081651643#, -0.02069094028031615#, 0.38313797190532994#, -0.013140261009786443#, 0.73016337479488913#, 1#, 0#, 0#, 0#)
    expectedPoints(24) = Array(0.38313797190532994#, -0.013140261009786443#, 0.73016337479488913#, 0.38334592018336089#, -0.014138379300656945#, 0.74011126489234669#, 0.38313797190532994#, -0.023090302662566703#, 0.7291650406284208#, 0.39313580954722349#, -0.013119500822704791#, 0.72995646539208592#)
    linkNames(25) = "thumb_metacarpal"
    expectedCounts(25) = 12
    homeData(25) = Array(0.020794827803092053#, -0.099811829087050108#, 0.99478900974575379#, -0.68149136531349497#, -0.72944856703503791#, -0.058943252825735037#, 0.73153065153812136#, -0.67671440565782803#, -0.083189657021677021#, 0.38313797190532994#, -0.013140261009786443#, 0.73016337479488913#, 1#, 0#, 0#, 0#)
    expectedPoints(25) = Array(0.38313797190532994#, -0.013140261009786443#, 0.73016337479488913#, 0.38334592018336089#, -0.014138379300656943#, 0.74011126489234669#, 0.37632305825219498#, -0.020434746680136822#, 0.72957394226663175#, 0.39045327842071115#, -0.019907405066364722#, 0.72933147822467237#)
    linkNames(26) = "thumb_proximal"
    expectedCounts(26) = 12
    homeData(26) = Array(0.020794827803092053#, -0.099811829087050108#, 0.99478900974575379#, -0.68149136531349497#, -0.72944856703503791#, -0.058943252825735037#, 0.73153065153812136#, -0.67671440565782803#, -0.083189657021677021#, 0.40508389145147361#, -0.033441693179521281#, 0.72766768508423885#, 1#, 0#, 0#, 0#)
    expectedPoints(26) = Array(0.40508389145147361#, -0.033441693179521281#, 0.72766768508423885#, 0.40529183972950455#, -0.034439811470391782#, 0.7376155751816964#, 0.39826897779833864#, -0.040736178849871657#, 0.72707825255598146#, 0.41239919796685481#, -0.040208837236099561#, 0.72683578851402209#)
    linkNames(27) = "thumb_distal"
    expectedCounts(27) = 10
    homeData(27) = Array(0.020794827803092053#, -0.099811829087050108#, 0.99478900974575379#, -0.68149136531349497#, -0.72944856703503791#, -0.058943252825735037#, 0.73153065153812136#, -0.67671440565782803#, -0.083189657021677021#, 0.41971450448223607#, -0.04697598129267784#, 0.72600389194380532#, 1#, 0#, 0#, 0#)
    expectedPoints(27) = Array(0.41971450448223607#, -0.04697598129267784#, 0.72600389194380532#, 0.41992245276026702#, -0.047974099583548341#, 0.73595178204126288#, 0.4128995908291011#, -0.054270466963028216#, 0.72541445941554794#, 0.42702981099761728#, -0.05374312534925612#, 0.72517199537358856#)
End Sub

Private Sub RestorePreferences()
    Dim result As Boolean
    If Not prefsCaptured Then Exit Sub
    On Error Resume Next
    Call swApp.SetUserPreferenceIntegerValue(swImportNeutralUnits, oldUnits)
    result = (swApp.GetUserPreferenceIntegerValue(swImportNeutralUnits) = oldUnits)
    If result = False Then LogLine "WARNING: could not restore import units"
    Call swApp.SetUserPreferenceIntegerValue(swImportNeutralAssemblyStructureMapping, oldMapping)
    result = (swApp.GetUserPreferenceIntegerValue(swImportNeutralAssemblyStructureMapping) = oldMapping)
    If Not result Then LogLine "WARNING: could not restore assembly mapping preference"
    Call swApp.SetUserPreferenceToggle(swImportNeutral_SolidandSurface, oldSolidSurface)
    result = (swApp.GetUserPreferenceToggle(swImportNeutral_SolidandSurface) = oldSolidSurface)
    If Not result Then LogLine "WARNING: could not restore solid/surface preference"
    Call swApp.SetUserPreferenceToggle(swImportNeutralRunDiagnostics, oldDiagnostics)
    result = (swApp.GetUserPreferenceToggle(swImportNeutralRunDiagnostics) = oldDiagnostics)
    If Not result Then LogLine "WARNING: could not restore diagnostic preference"
    Call swApp.SetUserPreferenceToggle(swMultiCAD_Enable3DInterconnect, oldInterconnect)
    result = (swApp.GetUserPreferenceToggle(swMultiCAD_Enable3DInterconnect) = oldInterconnect)
    If Not result Then LogLine "WARNING: could not restore 3D Interconnect preference"
    If Err.Number <> 0 Then LogLine "RESTORE_ERROR " & CStr(Err.Number) & " " & Err.Description
    prefsCaptured = False
    On Error GoTo 0
End Sub



Private Sub ConfigureImport()
    oldMapping = swApp.GetUserPreferenceIntegerValue(swImportNeutralAssemblyStructureMapping)
    oldUnits = swApp.GetUserPreferenceIntegerValue(swImportNeutralUnits)
    oldInterconnect = swApp.GetUserPreferenceToggle(swMultiCAD_Enable3DInterconnect)
    oldSolidSurface = swApp.GetUserPreferenceToggle(swImportNeutral_SolidandSurface)
    oldDiagnostics = swApp.GetUserPreferenceToggle(swImportNeutralRunDiagnostics)
    prefsCaptured = True
    Call swApp.SetUserPreferenceToggle(swMultiCAD_Enable3DInterconnect, False)
    Check swApp.GetUserPreferenceToggle(swMultiCAD_Enable3DInterconnect) = False, "Cannot disable 3D Interconnect"
    Call swApp.SetUserPreferenceIntegerValue(swImportNeutralAssemblyStructureMapping, swImportNeutralAssemblyStructureMapping_MultibodyPart)
    Check swApp.GetUserPreferenceIntegerValue(swImportNeutralAssemblyStructureMapping) = swImportNeutralAssemblyStructureMapping_MultibodyPart, "Cannot set multibody mapping"
    Call swApp.SetUserPreferenceIntegerValue(swImportNeutralUnits, swImportNeutralUnits_ImportFileUnits)
    Check swApp.GetUserPreferenceIntegerValue(swImportNeutralUnits) = swImportNeutralUnits_ImportFileUnits, "Cannot set file-specified units"
    Call swApp.SetUserPreferenceToggle(swImportNeutral_SolidandSurface, True)
    If swApp.GetUserPreferenceToggle(swImportNeutral_SolidandSurface) <> False Then
        LogLine "SOLID_SURFACE_PREFERENCE_READBACK=True"
    Else
        LogLine "PREFERENCE_WARNING: SolidandSurface readback False in this native session; continuing to actual strict geometry checks"
        LogLine "REQUIRED: each imported document must be Part, exact expected solid count, zero sheet bodies, correct gross mm scale"
    End If
    Call swApp.SetUserPreferenceToggle(swImportNeutralRunDiagnostics, False)
    Check swApp.GetUserPreferenceToggle(swImportNeutralRunDiagnostics) = False, "Cannot disable automatic healing"
    LogLine "PREFERENCES_SET: classic STEP, multibody part, source-file mm, no automatic healing"
End Sub

Private Sub ValidateTransform(ByVal linkIndex As Long, ByVal transform As SldWorks.MathTransform, ByVal stage As String)
    Dim point As SldWorks.MathPoint
    Dim pointData(2) As Double
    Dim vPoint As Variant, actual As Variant, expected As Variant
    Dim i As Long, axis As Long, errorM As Double, maximumError As Double
    Check Not transform Is Nothing, "Missing transform: " & linkNames(linkIndex)
    expected = expectedPoints(linkIndex)
    For i = 0 To 3
        For axis = 0 To 2
            pointData(axis) = 0#
        Next axis
        If i > 0 Then pointData(i - 1) = 0.01
        vPoint = pointData
        Set point = mathUtil.CreatePoint(vPoint)
        Check Not point Is Nothing, "CreatePoint failed"
        Set point = point.MultiplyTransform(transform)
        Check Not point Is Nothing, "MultiplyTransform failed"
        actual = point.ArrayData
        For axis = 0 To 2
            errorM = Abs(CDbl(actual(axis)) - CDbl(expected(i * 3 + axis)))
            If errorM > maximumError Then maximumError = errorM
        Next axis
    Next i
    LogLine linkNames(linkIndex) & " " & stage & " MATH_POINT_MAX_ERROR_M=" & CStr(maximumError)
    Check maximumError < 0.000000001, "Transform point check failed: " & linkNames(linkIndex) & " " & stage
End Sub

Private Function HomeTransform(ByVal linkIndex As Long) As SldWorks.MathTransform
    Dim data(15) As Double, values As Variant, arrayData As Variant
    Dim i As Long
    values = homeData(linkIndex)
    For i = 0 To 15
        data(i) = CDbl(values(i))
    Next i
    arrayData = data
    Set HomeTransform = mathUtil.CreateTransform(arrayData)
    Check Not HomeTransform Is Nothing, "CreateTransform failed: " & linkNames(linkIndex)
End Function

Private Sub SaveNew(ByVal model As SldWorks.ModelDoc2, ByVal destination As String)
    Dim result As Boolean, errors As Long, warnings As Long
    Check Len(Dir$(destination)) = 0, "Refusing existing destination: " & destination
    model.ClearSelection2 True
    result = model.Extension.SaveAs(destination, swSaveAsCurrentVersion, swSaveAsOptions_Silent, Nothing, errors, warnings)
    LogLine "SAVE " & destination & " RETURN=" & CStr(result) & " ERRORS=" & CStr(errors) & " WARNINGS=" & CStr(warnings)
    Check (result <> False), "Native save returned False: " & destination
    Check (errors = 0), "Native save reported errors: " & destination
    Check Len(Dir$(destination)) > 0, "Saved file missing: " & destination
    Check FileLen(destination) > 0, "Saved file empty: " & destination
    LogLine "SAVED_BYTES=" & CStr(FileLen(destination))
End Sub

Private Sub ImportOne(ByVal linkIndex As Long, ByVal inputFolder As String, ByVal outputFolder As String)
    Dim inputPath As String, stem As String
    Dim model As SldWorks.ModelDoc2, alreadyOpen As SldWorks.ModelDoc2
    Dim part As SldWorks.PartDoc, stepData As SldWorks.ImportStepData
    Dim body As SldWorks.Body2
    Dim bodies As Variant, sheets As Variant, box As Variant
    Dim loadErrors As Long, i As Long, axis As Long
    Dim low(2) As Double, high(2) As Double, largestSpan As Double, span As Double
    stem = linkNames(linkIndex)
    inputPath = inputFolder & stem & ".step"
    nativePaths(linkIndex) = outputFolder & stem & ".SLDPRT"
    LogLine "IMPORT_STARTED " & CStr(linkIndex + 1) & "/28 SOURCE=" & inputPath
    Set alreadyOpen = swApp.GetOpenDocumentByName(inputPath)
    Check alreadyOpen Is Nothing, "Source already open; close it before fresh import: " & inputPath
    Set stepData = swApp.GetImportFileData(inputPath)
    Check Not stepData Is Nothing, "No ImportStepData: " & stem
    stepData.MapConfigurationData = False
    Set model = swApp.LoadFile4(inputPath, "r", stepData, loadErrors)
    LogLine stem & " LOAD_ERRORS=" & CStr(loadErrors)
    Check Not model Is Nothing, "LoadFile4 returned Nothing: " & stem
    Check loadErrors = 0, "LoadFile4 error: " & stem
    Check model.GetType = swDocPART, "Expected one multibody Part: " & stem
    Set part = model
    bodies = part.GetBodies2(swSolidBody, False)
    sheets = part.GetBodies2(swSheetBody, False)
    LogLine stem & " SOLIDS=" & CStr(CountArray(bodies)) & " EXPECTED=" & CStr(expectedCounts(linkIndex)) & " SHEETS=" & CStr(CountArray(sheets))
    Check CountArray(bodies) = expectedCounts(linkIndex), "Wrong solid count: " & stem
    Check CountArray(sheets) = 0, "Unexpected sheet bodies: " & stem
    For axis = 0 To 2
        low(axis) = 1E+30
        high(axis) = -1E+30
    Next axis
    For i = LBound(bodies) To UBound(bodies)
        Set body = bodies(i)
        LogLine stem & " BODY=" & body.Name
        box = body.GetBodyBox
        Check IsArray(box), "No body bounding box: " & stem
        For axis = 0 To 2
            If CDbl(box(axis)) < low(axis) Then low(axis) = CDbl(box(axis))
            If CDbl(box(axis + 3)) > high(axis) Then high(axis) = CDbl(box(axis + 3))
        Next axis
    Next i
    For axis = 0 To 2
        span = high(axis) - low(axis)
        LogLine stem & " APPROX_MIN_MAX_SPAN_AXIS_" & CStr(axis) & "_MM=" & CStr(low(axis) * 1000#) & "," & CStr(high(axis) * 1000#) & "," & CStr(span * 1000#)
        If span > largestSpan Then largestSpan = span
    Next axis
    ' Gross scale gate only; approximate boxes are not precision dimensional evidence.
    Check largestSpan > 0.003 And largestSpan < 0.5, "Gross scale gate failed; expected each rigid link between 3 and 500 mm"
    SaveNew model, nativePaths(linkIndex)
    Set importedModels(linkIndex) = model
    LogLine stem & " IMPORT_COUNT_SCALE_SAVE_PASS; exact dimensions/geometry diagnostics pending"
End Sub

Private Function AssemblyTemplate() As String
    Dim path As String
    path = swApp.GetUserPreferenceStringValue(swDefaultTemplateAssembly)
    If Len(path) = 0 Then path = swApp.GetDocumentTemplate(swDocASSEMBLY, "", 0, 0#, 0#)
    Check Len(path) > 0, "No assembly template configured; create one blank assembly manually then rerun"
    Check Len(Dir$(path)) > 0, "Assembly template does not exist: " & path
    LogLine "ASSEMBLY_TEMPLATE=" & path
    AssemblyTemplate = path
End Function

Private Sub CreateStaticAssembly(ByVal outputFolder As String, ByVal templatePath As String)
    Dim model As SldWorks.ModelDoc2, assembly As SldWorks.AssemblyDoc
    Dim comp As SldWorks.Component2, transform As SldWorks.MathTransform
    Dim items As Variant, i As Long, result As Boolean
    Set model = swApp.NewDocument(templatePath, 0, 0#, 0#)
    Check Not model Is Nothing, "NewDocument failed for assembly template"
    Check model.GetType = swDocASSEMBLY, "Template did not create an Assembly"
    Set assembly = model
    For i = 0 To 27
        ' Imported parts remain open/in memory, as AddComponent5 requires.
        Set comp = assembly.AddComponent5(nativePaths(i), swAddComponentConfigOptions_CurrentSelectedConfig, "", False, "", 0#, 0#, 0#)
        Check Not comp Is Nothing, "AddComponent5 failed: " & linkNames(i)
        Set components(i) = comp
        model.ClearSelection2 True
        result = comp.Select4(False, Nothing, False)
        Check result, "Could not select component: " & linkNames(i)
        If comp.IsFixed Then assembly.UnfixComponent
        Check (comp.IsFixed = False), "Cannot float before positioning: " & linkNames(i)
        Set transform = HomeTransform(i)
        Set comp.Transform2 = transform
        Set transform = comp.Transform2
        ValidateTransform i, transform, "PLACEMENT_READBACK"
        model.ClearSelection2 True
        result = comp.Select4(False, Nothing, False)
        Check result, "Could not select component for static fixing: " & linkNames(i)
        assembly.FixComponent
        Check comp.IsFixed, "Static fixing failed: " & linkNames(i)
        LogLine "COMPONENT_PLACED_FIXED " & CStr(i + 1) & "/28 " & comp.Name2
    Next i
    model.ClearSelection2 True
    result = model.EditRebuild3
    LogLine "ASSEMBLY_REBUILD_RETURN=" & CStr(result)
    Check result, "Assembly rebuild reported failure"
    items = assembly.GetComponents(True)
    LogLine "TOP_LEVEL_COMPONENT_COUNT=" & CStr(CountArray(items))
    Check CountArray(items) = 28, "Wrong top-level component count"
    For i = 0 To 27
        Set transform = components(i).Transform2
        ValidateTransform i, transform, "POST_REBUILD_READBACK"
        Check components(i).IsFixed, "Component not fixed after rebuild: " & linkNames(i)
    Next i
    model.ShowNamedView2 "*Isometric", 7
    model.ViewZoomtofit2
    SaveNew model, outputFolder & "AnthroArm27_STATIC_HOME.SLDASM"
    LogLine "STATIC_ASSEMBLY_SAVED: 28 fixed components, 293 source solids; NO MATES OR MOTION"
End Sub

' Sole public no-argument entry point.
Public Sub main()
    Dim macroPath As String, folder As String, outputFolder As String, runStamp As String
    Dim templatePath As String, failureText As String, failureNumber As Long
    Dim i As Long, total As Long, transform As SldWorks.MathTransform
    On Error GoTo Failed
    Set swApp = Application.SldWorks
    macroPath = swApp.GetCurrentMacroPathName()
    Check Len(macroPath) > 0 And InStrRev(macroPath, "\") > 0, "Save running macro before running main"
    folder = Left$(macroPath, InStrRev(macroPath, "\"))
    runStamp = Format$(Now, "yyyymmdd_hhnnss") & "_" & CStr(CLng(Timer * 1000#))
    outputFolder = folder & "AnthroArm27_Static_" & runStamp & "\"
    Check Len(Dir$(Left$(outputFolder, Len(outputFolder) - 1), vbDirectory)) = 0, "Refusing existing output folder"
    MkDir Left$(outputFolder, Len(outputFolder) - 1)
    runtimeLog = outputFolder & "Native_Static_Build.log"
    Check Len(Dir$(runtimeLog)) = 0, "Refusing existing log"
    logReady = True
    LogLine "RUN_STARTED: static native import and placement; not joints/motion/FEA"
    LogLine "MACRO_PATH=" & macroPath
    LogLine "OUTPUT_FOLDER=" & outputFolder
    LogLine "MACRO_VERSION=AutoFullArmStaticV3"
    LogLine "SOLIDWORKS_REVISION=" & swApp.RevisionNumber
    InitData
    For i = 0 To 27
        Check Len(Dir$(folder & linkNames(i) & ".step")) > 0, "Missing flat sibling STEP: " & linkNames(i)
        total = total + expectedCounts(i)
    Next i
    Check total = 293, "Embedded body counts inconsistent"
    LogLine "PREFLIGHT: all 28 STEP inputs present; expected 293 solid bodies"
    templatePath = AssemblyTemplate()
    Set mathUtil = swApp.GetMathUtility
    Check Not mathUtil Is Nothing, "Cannot access MathUtility"
    For i = 0 To 27
        Set transform = HomeTransform(i)
        ValidateTransform i, transform, "NATIVE_MATH_PRECHECK"
    Next i
    ConfigureImport
    For i = 0 To 27
        ImportOne i, folder, outputFolder
    Next i
    RestorePreferences
    CreateStaticAssembly outputFolder, templatePath
    LogLine "COMPLETED_STATIC_STAGE_ONLY"
    LogLine "PENDING: reopen verification, native dimensions/Import Diagnostics, actual joint mates, interference, Motion, FEA, hardware"
    MsgBox "Static native arm saved: 28 parts + assembly + log." & vbCrLf & outputFolder & vbCrLf & "All components fixed. No mates, Motion or FEA performed.", vbInformation
    logReady = False
    Exit Sub
Failed:
    failureNumber = Err.Number
    failureText = Err.Description
    On Error Resume Next
    LogLine "FAIL " & CStr(failureNumber) & " | " & failureText
    LogLine "Partial outputs preserved; complete static stage did not pass."
    RestorePreferences
    MsgBox "AutoFullArmStaticV3 stopped: " & CStr(failureNumber) & vbCrLf & failureText & vbCrLf & "Log: " & runtimeLog, vbExclamation
    logReady = False
End Sub
