import copy
import xml.etree.ElementTree as et

from kk_plap_generator.generator.utils import keyframe_get, keyframe_set

# This dataset assumes pulled out at Y: 0.2, pushed in at Y: 0.1, out_direction == 1


keyframes_sets = {
    "simple": et.Element("interpolable"),
    "under_push": et.Element("interpolable"),
    "over_push": et.Element("interpolable"),
    "under_pull": et.Element("interpolable"),
    "over_pull": et.Element("interpolable"),
}
keyframes_sets["simple"].extend(
    [
        et.Element("keyframe", time="0.0", valueX="0", valueY="0.2", valueZ="0"),
        # reference
        et.Element("keyframe", time="0.2", valueX="0", valueY="0.1", valueZ="0"),
        et.Element("keyframe", time="0.4", valueX="0", valueY="0.2", valueZ="0"),
        et.Element("keyframe", time="0.6", valueX="0", valueY="0.1", valueZ="0"),
        et.Element("keyframe", time="0.8", valueX="0", valueY="0.2", valueZ="0"),
    ]
)
keyframes_sets["simple_w_curve"] = copy.deepcopy(keyframes_sets["simple"])
for keyframe in keyframes_sets["simple_w_curve"]:
    keyframe.extend(
        [
            et.Element("curve", time="0", value="0.0", inTangent="0.0", outTangent="0.0"),
            et.Element(
                "curve", time="0.5", value="1.0", inTangent="0.0", outTangent="0.0"
            ),
            et.Element(
                "curve", time="0.90", value="0.0", inTangent="0.0", outTangent="0.0"
            ),
        ]
    )
keyframes_sets["under_push"].extend(
    [
        et.Element("keyframe", time="0.0", valueX="0", valueY="0.2", valueZ="0"),
        # reference
        et.Element("keyframe", time="0.2", valueX="0", valueY="0.1", valueZ="0"),
        et.Element("keyframe", time="0.4", valueX="0", valueY="0.2", valueZ="0"),
        et.Element("keyframe", time="0.6", valueX="0", valueY="0.12", valueZ="0"),
        et.Element("keyframe", time="0.8", valueX="0", valueY="0.2", valueZ="0"),
        et.Element("keyframe", time="1.0", valueX="0", valueY="0.15", valueZ="0"),
        et.Element("keyframe", time="1.2", valueX="0", valueY="0.2", valueZ="0"),
        et.Element("keyframe", time="1.4", valueX="0", valueY="0.18", valueZ="0"),
        et.Element("keyframe", time="1.6", valueX="0", valueY="0.2", valueZ="0"),
        et.Element("keyframe", time="1.8", valueX="0", valueY="0.19", valueZ="0"),
    ]
)
keyframes_sets["over_push"].extend(
    [
        et.Element("keyframe", time="0.0", valueX="0", valueY="0.2", valueZ="0"),
        et.Element("keyframe", time="0.2", valueX="0", valueY="0.1", valueZ="0"),
        et.Element("keyframe", time="0.4", valueX="0", valueY="0.2", valueZ="0"),
        et.Element("keyframe", time="0.6", valueX="0", valueY="0.08", valueZ="0"),
        et.Element("keyframe", time="0.8", valueX="0", valueY="0.2", valueZ="0"),
    ]
)
keyframes_sets["under_pull"].extend(
    [
        et.Element("keyframe", time="0.0", valueX="0", valueY="0.2", valueZ="0"),
        et.Element("keyframe", time="0.2", valueX="0", valueY="0.1", valueZ="0"),
        et.Element("keyframe", time="0.3", valueX="0", valueY="0.2", valueZ="0"),
        et.Element("keyframe", time="0.35", valueX="0", valueY="0.1", valueZ="0"),
        et.Element("keyframe", time="0.4", valueX="0", valueY="0.18", valueZ="0"),
        et.Element("keyframe", time="0.6", valueX="0", valueY="0.1", valueZ="0"),
        et.Element("keyframe", time="0.8", valueX="0", valueY="0.15", valueZ="0"),
        et.Element("keyframe", time="1.0", valueX="0", valueY="0.1", valueZ="0"),
        et.Element("keyframe", time="1.2", valueX="0", valueY="0.12", valueZ="0"),
        et.Element("keyframe", time="1.4", valueX="0", valueY="0.1", valueZ="0"),
        et.Element("keyframe", time="1.6", valueX="0", valueY="0.11", valueZ="0"),
        et.Element("keyframe", time="1.8", valueX="0", valueY="0.1", valueZ="0"),
    ]
)
keyframes_sets["over_pull"].extend(
    [
        et.Element("keyframe", time="0.0", valueX="0", valueY="0.2", valueZ="0"),
        et.Element("keyframe", time="0.2", valueX="0", valueY="0.1", valueZ="0"),
        et.Element("keyframe", time="0.4", valueX="0", valueY="0.2", valueZ="0"),
        et.Element("keyframe", time="0.6", valueX="0", valueY="0.1", valueZ="0"),
        et.Element("keyframe", time="0.8", valueX="0", valueY="0.22", valueZ="0"),
        et.Element("keyframe", time="1.0", valueX="0", valueY="0.1", valueZ="0"),
    ]
)


curve_keyframe_simple_sets = {
    "basic_2frames": et.Element("interpolable"),
    "one_plap_no_reset": et.Element("interpolable"),
    "one_plap_w_reset": et.Element("interpolable"),
    "multi_plap_w_reset": et.Element("interpolable"),
    "multi_plap_over_push": et.Element("interpolable"),
    "multi_plap_under_push": et.Element("interpolable"),
    "multi_plap_over_pull": et.Element("interpolable"),
    "multi_plap_under_pull": et.Element("interpolable"),
}
curve_keyframe_simple_sets["basic_2frames"].extend(
    [
        et.Element("curve", time="0", value="0.0", inTangent="0.0", outTangent="0.0"),
        et.Element("curve", time="1.0", value="1.0", inTangent="0.0", outTangent="0.0"),
    ]
)
curve_keyframe_simple_sets["one_plap_no_reset"].extend(
    [
        et.Element("curve", time="0", value="0.0", inTangent="0.0", outTangent="0.0"),
        et.Element("curve", time="0.5", value="1.0", inTangent="0.0", outTangent="0.0"),
        et.Element("curve", time="0.8", value="0.9", inTangent="0.0", outTangent="0.0"),
    ]
)
curve_keyframe_simple_sets["one_plap_w_reset"].extend(
    [
        et.Element("curve", time="0", value="0.0", inTangent="0.0", outTangent="0.0"),
        et.Element("curve", time="0.5", value="1.0", inTangent="0.0", outTangent="0.0"),
        et.Element("curve", time="0.8", value="0.0", inTangent="0.0", outTangent="0.0"),
    ]
)
curve_keyframe_simple_sets["multi_plap_w_reset"].extend(
    [
        et.Element("curve", time="0", value="0.0", inTangent="0.0", outTangent="0.0"),
        et.Element("curve", time="0.25", value="1.0", inTangent="0.0", outTangent="0.0"),
        et.Element("curve", time="0.5", value="0.0", inTangent="0.0", outTangent="0.0"),
        et.Element("curve", time="0.75", value="1.0", inTangent="0.0", outTangent="0.0"),
        et.Element("curve", time="0.90", value="0.0", inTangent="0.0", outTangent="0.0"),
    ]
)
curve_keyframe_simple_sets["multi_plap_over_push"].extend(
    [
        et.Element("curve", time="0", value="0.0", inTangent="0.0", outTangent="0.0"),
        et.Element("curve", time="0.25", value="1.1", inTangent="0.0", outTangent="0.0"),
        et.Element("curve", time="0.5", value="0.0", inTangent="0.0", outTangent="0.0"),
        et.Element("curve", time="0.75", value="1.2", inTangent="0.0", outTangent="0.0"),
        et.Element("curve", time="0.90", value="0.0", inTangent="0.0", outTangent="0.0"),
        et.Element("curve", time="1.0", value="2.0", inTangent="0.0", outTangent="0.0"),
    ]
)
curve_keyframe_simple_sets["multi_plap_under_push"].extend(
    [
        et.Element("curve", time="0", value="0.0", inTangent="0.0", outTangent="0.0"),
        et.Element("curve", time="0.25", value="0.9", inTangent="0.0", outTangent="0.0"),
        et.Element("curve", time="0.5", value="0.0", inTangent="0.0", outTangent="0.0"),
        et.Element("curve", time="0.75", value="0.85", inTangent="0.0", outTangent="0.0"),
        et.Element("curve", time="0.90", value="0.0", inTangent="0.0", outTangent="0.0"),
        et.Element("curve", time="1.0", value="0.9", inTangent="0.0", outTangent="0.0"),
    ]
)
curve_keyframe_simple_sets["multi_plap_over_pull"].extend(
    [
        et.Element("curve", time="0", value="0.0", inTangent="0.0", outTangent="0.0"),
        et.Element("curve", time="0.25", value="1.0", inTangent="0.0", outTangent="0.0"),
        et.Element("curve", time="0.5", value="-1.0", inTangent="0.0", outTangent="0.0"),
        et.Element("curve", time="0.75", value="1.0", inTangent="0.0", outTangent="0.0"),
        et.Element("curve", time="0.90", value="-1.0", inTangent="0.0", outTangent="0.0"),
    ]
)
curve_keyframe_simple_sets["multi_plap_under_pull"].extend(
    [
        et.Element("curve", time="0", value="0.15", inTangent="0.0", outTangent="0.0"),
        et.Element("curve", time="0.25", value="1.0", inTangent="0.0", outTangent="0.0"),
        et.Element("curve", time="0.5", value="0.15", inTangent="0.0", outTangent="0.0"),
        et.Element("curve", time="0.75", value="1.0", inTangent="0.0", outTangent="0.0"),
        et.Element("curve", time="0.90", value="0.15", inTangent="0.0", outTangent="0.0"),
    ]
)


keyframes_w_curves_sets = {}

keyframes_w_curves_sets["simple"] = copy.deepcopy(keyframes_sets["simple"])
for keyframe in keyframes_w_curves_sets["simple"]:
    keyframe.extend(copy.deepcopy(curve_keyframe_simple_sets["one_plap_w_reset"]))

keyframes_w_curves_sets["under_push"] = copy.deepcopy(keyframes_sets["simple"])
for keyframe in keyframes_w_curves_sets["under_push"]:
    if keyframe_get(keyframe, "time") % 0.4 != 0.0:
        keyframe_set(keyframe, "valueY", keyframe_get(keyframe, "valueY") * 1.2)

    keyframe.extend(copy.deepcopy(curve_keyframe_simple_sets["one_plap_w_reset"]))

keyframes_w_curves_sets["over_push"] = copy.deepcopy(keyframes_sets["simple"])
for keyframe in keyframes_w_curves_sets["over_push"]:
    if keyframe_get(keyframe, "time") % 0.4 != 0.0:
        keyframe_set(keyframe, "valueY", keyframe_get(keyframe, "valueY") * 0.5)

    keyframe.extend(copy.deepcopy(curve_keyframe_simple_sets["one_plap_w_reset"]))

keyframes_w_curves_sets["under_pull"] = copy.deepcopy(keyframes_sets["simple"])
for keyframe in keyframes_w_curves_sets["under_pull"]:
    if keyframe_get(keyframe, "time") % 0.4 == 0.0:
        keyframe_set(keyframe, "valueY", keyframe_get(keyframe, "valueY") * 0.85)

    keyframe.extend(copy.deepcopy(curve_keyframe_simple_sets["one_plap_w_reset"]))

keyframes_w_curves_sets["over_pull"] = copy.deepcopy(keyframes_sets["simple"])
for keyframe in keyframes_w_curves_sets["over_pull"]:
    if keyframe_get(keyframe, "time") % 0.4 == 0.0:
        keyframe_set(keyframe, "valueY", keyframe_get(keyframe, "valueY") * 2.0)

    keyframe.extend(copy.deepcopy(curve_keyframe_simple_sets["one_plap_w_reset"]))


# root = et.Element("root")
# for key, value in keyframes_w_curves_sets.items():
#     root.append(value)
# tree = et.ElementTree(root)
# tree.write("tt.xml")

# parse et from string

eletree = et.Element("""
<interpolable enabled="true" owner="Timeline" objectIndex="2" id="guideObjectPos" guideObjectPath="cf_t_hips(work)" bgColorR="0.882353" bgColorG="0" bgColorB="0" alias="胴体">
		<keyframe time="0.04" valueX="-2.38418579E-07" valueY="0.151186466" valueZ="0.3253969">
			<curveKeyframe time="0" value="0" inTangent="0" outTangent="1"/>
			<curveKeyframe time="0.0669013038" value="0.876761" inTangent="0" outTangent="0"/>
			<curveKeyframe time="0.192091137" value="0.865493238" inTangent="-5.67128038" outTangent="0"/>
			<curveKeyframe time="0.212697491" value="0.0669016242" inTangent="0" outTangent="29.5461979"/>
			<curveKeyframe time="0.2704226" value="0.0753524154" inTangent="0" outTangent="0"/>
			<curveKeyframe time="0.420129746" value="1" inTangent="-5.67128038" outTangent="0"/>
			<curveKeyframe time="0.4622532" value="0" inTangent="0" outTangent="28.6362553"/>
			<curveKeyframe time="0.511267662" value="0.0204227064" inTangent="0" outTangent="0"/>
			<curveKeyframe time="0.58" value="0.9500003" inTangent="-5.67128038" outTangent="0"/>
			<curveKeyframe time="0.6042253" value="0.0500002578" inTangent="0" outTangent="28.6362553"/>
			<curveKeyframe time="0.6464789" value="0.06267623" inTangent="0" outTangent="0"/>
			<curveKeyframe time="0.771809161" value="0.88662" inTangent="-5.67128038" outTangent="0"/>
			<curveKeyframe time="0.7985915" value="0.0542255454" inTangent="0" outTangent="28.6362553"/>
			<curveKeyframe time="0.8408451" value="0.06267623" inTangent="0" outTangent="0"/>
			<curveKeyframe time="1" value="1" inTangent="-5.67128038" outTangent="0"/>
		</keyframe>
		<keyframe time="6.04" valueX="1.86264515E-08" valueY="0.312773943" valueZ="0.357165039">
			<curveKeyframe time="0" value="0" inTangent="0" outTangent="0"/>
			<curveKeyframe time="0.6507041" value="0.121831223" inTangent="0" outTangent="0"/>
			<curveKeyframe time="1" value="1" inTangent="0" outTangent="0"/>
		</keyframe>
		<keyframe time="7.055" valueX="-3.7252903E-09" valueY="0.118988812" valueZ="0.27029413">
			<curveKeyframe time="0" value="0" inTangent="0" outTangent="0"/>
			<curveKeyframe time="0.192091137" value="0.865493238" inTangent="-5.67128038" outTangent="0"/>
			<curveKeyframe time="0.212697491" value="0" inTangent="0" outTangent="29.5461979"/>
			<curveKeyframe time="0.2704226" value="0" inTangent="0" outTangent="0"/>
			<curveKeyframe time="0.420129746" value="1" inTangent="-5.67128038" outTangent="0"/>
			<curveKeyframe time="0.4622532" value="0" inTangent="0" outTangent="28.6362553"/>
			<curveKeyframe time="0.511267662" value="0" inTangent="0" outTangent="0"/>
			<curveKeyframe time="0.58" value="0.9500003" inTangent="-5.67128038" outTangent="0"/>
			<curveKeyframe time="0.6042253" value="0" inTangent="0" outTangent="28.6362553"/>
			<curveKeyframe time="0.6464789" value="0" inTangent="0" outTangent="0"/>
			<curveKeyframe time="0.771809161" value="1" inTangent="-5.67128038" outTangent="0"/>
			<curveKeyframe time="0.7985915" value="0" inTangent="0" outTangent="28.6362553"/>
			<curveKeyframe time="0.8408451" value="0" inTangent="0" outTangent="0"/>
			<curveKeyframe time="1" value="1" inTangent="-5.67128038" outTangent="0"/>
		</keyframe>
		<keyframe time="12.4331455" valueX="-0.0004711151" valueY="0.303227663" valueZ="0.2762437">
			<curveKeyframe time="0" value="0" inTangent="2" outTangent="2"/>
			<curveKeyframe time="0.41760543" value="0.155634269" inTangent="0" outTangent="0"/>
			<curveKeyframe time="0.5274646" value="0.265493542" inTangent="0" outTangent="9.369087"/>
			<curveKeyframe time="1" value="1" inTangent="0" outTangent="0"/>
		</keyframe>
		<keyframe time="12.9215965" valueX="-3.7252903E-09" valueY="0.118988812" valueZ="0.27029413">
			<curveKeyframe time="0" value="0" inTangent="0" outTangent="0"/>
			<curveKeyframe time="0.192091137" value="0.865493238" inTangent="-5.67128038" outTangent="0"/>
			<curveKeyframe time="0.212697491" value="0" inTangent="0" outTangent="29.5461979"/>
			<curveKeyframe time="0.2704226" value="0" inTangent="0" outTangent="0"/>
			<curveKeyframe time="0.420129746" value="1" inTangent="-5.67128038" outTangent="0"/>
			<curveKeyframe time="0.4622532" value="0" inTangent="0" outTangent="28.6362553"/>
			<curveKeyframe time="0.511267662" value="0" inTangent="0" outTangent="0"/>
			<curveKeyframe time="0.58" value="0.9500003" inTangent="-5.67128038" outTangent="0"/>
			<curveKeyframe time="0.6042253" value="0" inTangent="0" outTangent="28.6362553"/>
			<curveKeyframe time="0.6464789" value="0" inTangent="0" outTangent="0"/>
			<curveKeyframe time="0.771809161" value="1" inTangent="-5.67128038" outTangent="0"/>
			<curveKeyframe time="0.7985915" value="0" inTangent="0" outTangent="28.6362553"/>
			<curveKeyframe time="0.8408451" value="0" inTangent="0" outTangent="0"/>
			<curveKeyframe time="1" value="1" inTangent="-5.67128038" outTangent="0"/>
		</keyframe>
		<keyframe time="15.4506531" valueX="-0.0004711151" valueY="0.303227663" valueZ="0.2762437">
			<curveKeyframe time="0" value="0" inTangent="2" outTangent="2"/>
			<curveKeyframe time="0.41760543" value="0.155634269" inTangent="0" outTangent="0"/>
			<curveKeyframe time="0.5274646" value="0.265493542" inTangent="0" outTangent="9.369087"/>
			<curveKeyframe time="1" value="1" inTangent="0" outTangent="0"/>
		</keyframe>
		<keyframe time="15.9391041" valueX="-3.7252903E-09" valueY="0.118988812" valueZ="0.27029413">
			<curveKeyframe time="0" value="0" inTangent="0" outTangent="0"/>
			<curveKeyframe time="0.192091137" value="0.865493238" inTangent="-5.67128038" outTangent="0"/>
			<curveKeyframe time="0.212697491" value="0" inTangent="0" outTangent="29.5461979"/>
			<curveKeyframe time="0.2704226" value="0" inTangent="0" outTangent="0"/>
			<curveKeyframe time="0.420129746" value="1" inTangent="-5.67128038" outTangent="0"/>
			<curveKeyframe time="0.4622532" value="0" inTangent="0" outTangent="28.6362553"/>
			<curveKeyframe time="0.511267662" value="0" inTangent="0" outTangent="0"/>
			<curveKeyframe time="0.58" value="0.9500003" inTangent="-5.67128038" outTangent="0"/>
			<curveKeyframe time="0.6042253" value="0" inTangent="0" outTangent="28.6362553"/>
			<curveKeyframe time="0.6464789" value="0" inTangent="0" outTangent="0"/>
			<curveKeyframe time="0.771809161" value="1" inTangent="-5.67128038" outTangent="0"/>
			<curveKeyframe time="0.7985915" value="0" inTangent="0" outTangent="28.6362553"/>
			<curveKeyframe time="0.8408451" value="0" inTangent="0" outTangent="0"/>
			<curveKeyframe time="1" value="1" inTangent="-5.67128038" outTangent="0"/>
		</keyframe>
		<keyframe time="18.17991" valueX="-0.0004711151" valueY="0.303227663" valueZ="0.2762437">
			<curveKeyframe time="0" value="0" inTangent="0" outTangent="0"/>
			<curveKeyframe time="1" value="1" inTangent="0" outTangent="0"/>
		</keyframe>
		<keyframe time="18.51979" valueX="0.0233910084" valueY="0.138792872" valueZ="0.2702942">
			<curveKeyframe time="0" value="0" inTangent="0" outTangent="0"/>
			<curveKeyframe time="0.06690173" value="0.902113259" inTangent="0" outTangent="5.67128038"/>
			<curveKeyframe time="0.164084852" value="0.8514091" inTangent="0" outTangent="0"/>
			<curveKeyframe time="0.3500003" value="0.5683104" inTangent="0" outTangent="0"/>
			<curveKeyframe time="0.493662328" value="0.669718862" inTangent="0" outTangent="0"/>
			<curveKeyframe time="0.5528172" value="0.5683104" inTangent="0" outTangent="0"/>
			<curveKeyframe time="0.6161975" value="0.7288738" inTangent="0" outTangent="0"/>
			<curveKeyframe time="0.6753524" value="0.564085066" inTangent="0" outTangent="0"/>
			<curveKeyframe time="0.7387327" value="0.661268234" inTangent="0" outTangent="0"/>
			<curveKeyframe time="0.88662" value="0.179578" inTangent="0" outTangent="0"/>
			<curveKeyframe time="1" value="1" inTangent="0" outTangent="0"/>
		</keyframe>
		<keyframe time="20.8063583" valueX="-0.0004711151" valueY="0.203227684" valueZ="0.326243669">
			<curveKeyframe time="0" value="0" inTangent="0" outTangent="0"/>
			<curveKeyframe time="0.113380536" value="0.2345076" inTangent="0" outTangent="0"/>
			<curveKeyframe time="0.273943931" value="0.175352708" inTangent="0" outTangent="0"/>
			<curveKeyframe time="0.3415496" value="0.3654935" inTangent="0" outTangent="0"/>
			<curveKeyframe time="0.4598594" value="0.302113235" inTangent="0" outTangent="0"/>
			<curveKeyframe time="0.5232397" value="0.5091555" inTangent="0" outTangent="0"/>
			<curveKeyframe time="0.6500002" value="0.441549867" inTangent="0" outTangent="0"/>
			<curveKeyframe time="0.7302821" value="0.6739442" inTangent="0" outTangent="0"/>
			<curveKeyframe time="0.80633837" value="0.6147893" inTangent="0" outTangent="0"/>
			<curveKeyframe time="0.8570427" value="0.8429583" inTangent="0" outTangent="0"/>
			<curveKeyframe time="0.9457748" value="0.7711273" inTangent="0" outTangent="0"/>
			<curveKeyframe time="1" value="1" inTangent="0" outTangent="0"/>
		</keyframe>
		<keyframe time="22.0600014" valueX="-2.38418579E-07" valueY="0.151186466" valueZ="0.3253969">
			<curveKeyframe time="0" value="0" inTangent="0" outTangent="1"/>
			<curveKeyframe time="0.0669013038" value="0.876761" inTangent="0" outTangent="0"/>
			<curveKeyframe time="0.192091137" value="0.865493238" inTangent="-5.67128038" outTangent="0"/>
			<curveKeyframe time="0.212697491" value="0.0669016242" inTangent="0" outTangent="29.5461979"/>
			<curveKeyframe time="0.2704226" value="0.0753524154" inTangent="0" outTangent="0"/>
			<curveKeyframe time="0.420129746" value="1" inTangent="-5.67128038" outTangent="0"/>
			<curveKeyframe time="0.4622532" value="0" inTangent="0" outTangent="28.6362553"/>
			<curveKeyframe time="0.511267662" value="0.0204227064" inTangent="0" outTangent="0"/>
			<curveKeyframe time="0.58" value="0.9500003" inTangent="-5.67128038" outTangent="0"/>
			<curveKeyframe time="0.6042253" value="0.0500002578" inTangent="0" outTangent="28.6362553"/>
			<curveKeyframe time="0.6464789" value="0.06267623" inTangent="0" outTangent="0"/>
			<curveKeyframe time="0.771809161" value="0.88662" inTangent="-5.67128038" outTangent="0"/>
			<curveKeyframe time="0.7985915" value="0.0542255454" inTangent="0" outTangent="28.6362553"/>
			<curveKeyframe time="0.8408451" value="0.06267623" inTangent="0" outTangent="0"/>
			<curveKeyframe time="1" value="1" inTangent="-5.67128038" outTangent="0"/>
		</keyframe>
	</interpolable>

""")
