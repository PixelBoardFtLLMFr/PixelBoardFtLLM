import file_manager as fm
import statistics
import os
import traceback
import ast
import json
from scipy import stats
import dabest
import numpy as np
import pingouin as pg
import matplotlib.pyplot as plt
import seaborn as sns
import itertools

def stat_test(data1, data2):
    _, p1 = stats.shapiro(data1)
    _, p2 = stats.shapiro(data2)
    
    shapiro_threshold = 0.05
    is_normal = p1 > shapiro_threshold and p2 > shapiro_threshold
    # print(">>> Shapiro p for data1:", p1)
    # print(">>> Shapiro p for data2:", p2)
    
    if is_normal:
        print("ttest _____________")
        _, p = stats.ttest_rel(data1, data2)
        eff_size = dabest.effsize.cohens_h(data1, data2)
        eff_desc = "small" if eff_size <= 0.2 else "medium" if eff_size <= 0.5 else "large"
    else:
        print("wilcoxon _____________")
        val = pg.wilcoxon(data1, data2, alternative='two-sided')
        p = val['p-val'].values[0]
        eff_size = val['RBC'].values[0]
        eff_desc = "small" if abs(eff_size) < 0.3 else "medium" if abs(eff_size) < 0.5 else "large"
        
    p_value_threshold = 0.05
    
    # if p < p_value_threshold:
    #     print(">>> Significant difference, p-value:", p)
    #     print(">>> Effect size:", eff_size)
    #     if p < 0.001:
    #         print(">>> Significant difference at 0.001")
    #     if p < 0.01:
    #         print(">>> Significant difference at 0.01")
    # else:
    #     print("No significant difference")
        
    eff_size = eff_size if p < p_value_threshold else 'no_difference'
    eff_desc = eff_desc if p < p_value_threshold else 'no_difference'
    
    return p1, p2, p, eff_size, eff_desc

def evaluate_angles(angles_str:str, target_length:int, min_val, max_val):
    try:
        angles=ast.literal_eval(angles_str)
        flattened_array = list(itertools.chain.from_iterable(angles))

        incorrect_dimensions=[a for a in angles if len(a)!=target_length]
        out_of_limits=[a for a in flattened_array if a<min_val or a>max_val]

        if len(incorrect_dimensions)>0:
            print(">>> incorrect dimension")
        if len(out_of_limits)>0:
            print(">>> out of limits")

        return len(incorrect_dimensions)<=0 and len(out_of_limits)<=0
        # for a in angles:
        #     if len(a)!=target_length:
        #         return False
        # return True
    except Exception as error:
        print(traceback.format_exc())
    return False

def evaluate_facial_expression(fe:str):
    available_fes=[
        "neutral",
        "happy",
        "sad",
        "angry",
        "surprised"
    ]

    if fe.lower() not in available_fes:
        print(f">>> wrong FE: {fe.lower()}")

    return fe.lower() in available_fes

def evaluate_vfx(vfx:str):
    available_vfxs=["angry",
                    "heart",
                    "sleepy",
                    "spark",
                    "sweat",
                    "cloud",
                    "none"]
    
    if vfx.lower() not in available_vfxs:
        print(f">>> wrong VFX: {vfx.lower}")

    return vfx.lower() in available_vfxs

def evaluate_segmented_data(arms, legs, head, y_pos, fe, vfx)->int:
    try:
        if evaluate_angles(angles_str=arms, target_length=2, min_val=-180, max_val=180)==False:
            return 0
        if evaluate_angles(angles_str=legs, target_length=2, min_val=-180, max_val=180)==False:
            return 0
        if evaluate_angles(angles_str=head, target_length=1, min_val=-90, max_val=90)==False:
            return 0
        if evaluate_angles(angles_str=y_pos, target_length=1, min_val=float('-inf'), max_val=float('inf'))==False:
            return 0
        if evaluate_facial_expression(fe=fe)==False:
            return 0
        if evaluate_vfx(vfx=vfx)==False:
            return 0
        return 1
    except Exception as error:
        print(traceback.format_exc())
    return 0

def evaluate_compiled_data(data)->int:
    try:
        myjson=data['response']
        myjson=myjson.replace("```", "")
        myjson=json.loads(myjson)
        if evaluate_angles(angles_str=str(myjson["arms"]), target_length=2, min_val=-180, max_val=180)==False:
            return 0
        if evaluate_angles(angles_str=str(myjson["legs"]), target_length=2, min_val=-180, max_val=180)==False:
            return 0
        if evaluate_angles(angles_str=str(myjson["head"]), target_length=1, min_val=-90, max_val=90)==False:
            return 0
        if evaluate_angles(angles_str=str(myjson["y_position"]), target_length=1, min_val=float('-inf'), max_val=float('inf'))==False:
            return 0
        if evaluate_facial_expression(fe=myjson["facial_expression"])==False:
            return 0
        if evaluate_vfx(vfx=myjson["visual_effect"])==False:
            return 0
        return 1
    except Exception as error:
        print(traceback.format_exc())
    return 0

def correct_rate_evaluation():
    compiled=fm.get_files_with_extensions(directory="./responses/compiled", extensions=["json"])
    compiled=[fm.read_json(path=c) for c in compiled]
    segmented=[]
    for i in range(len(compiled)):
        t_segmented={"arms": fm.read_json(path=f"./responses/segmented/{(i+1)}-arms.json"),
                     "legs": fm.read_json(path=f"./responses/segmented/{(i+1)}-legs.json"),
                     "head": fm.read_json(path=f"./responses/segmented/{(i+1)}-head.json"),
                     "y_position": fm.read_json(path=f"./responses/segmented/{(i+1)}-y_position.json"),
                     "facial_expression": fm.read_json(path=f"./responses/segmented/{(i+1)}-facial_expression.json"),
                     "visual_effect": fm.read_json(path=f"./responses/segmented/{(i+1)}-visual_effect.json")}
        segmented.append(t_segmented)
    
    header=["n", "segmented", "compiled"]
    rows=[]
    s_rates=[]
    c_rates=[]
    # print(len(segmented))
    for i in range(len(compiled)):
        s_correct=evaluate_segmented_data(arms=segmented[i]["arms"]["response"],
                                          legs=segmented[i]["legs"]["response"],
                                          head=segmented[i]["head"]["response"],
                                          y_pos=segmented[i]["y_position"]["response"],
                                          fe=segmented[i]["facial_expression"]["response"],
                                          vfx=segmented[i]["visual_effect"]["response"])
        c_correct=evaluate_compiled_data(data=compiled[i])

        s_rates.append(s_correct)
        c_rates.append(c_correct)
        rows.append([i+1, s_correct, c_correct])
    
    p1, p2, p, eff_size, eff_desc = stat_test(data1=s_rates, data2=c_rates)
    rows.append(["mean", statistics.mean(s_rates), statistics.mean(c_rates)])
    rows.append(["statistical_difference", p, ""])
    rows.append(["effect_size", eff_size, eff_desc])

    fm.write_csv(path=os.path.join("evaluation", "correct_rates.csv"), data=rows, header=header)
    pass

def response_time_evaluation():
    segmented=fm.get_files_with_extensions(directory="./responses/segmented", extensions=["json"])
    segmented=[s for s in segmented if "arms" in s]
    compiled=fm.get_files_with_extensions(directory="./responses/compiled", extensions=["json"])

    header=["n", "segmented", "compiled"]
    rows=[]

    s_durations=[]
    c_durations=[]
    for i in range(len(segmented)):
        s_data=fm.read_json(segmented[i])
        c_data=fm.read_json(compiled[i])
        # print(s_data)

        s_duration=s_data['duration']
        c_duration=c_data['duration']

        s_durations.append(s_duration)
        c_durations.append(c_duration)
        rows.append([i+1, s_duration, c_duration])
    p1, p2, p, eff_size, eff_desc = stat_test(data1=s_durations, data2=c_durations)
    rows.append(["mean", statistics.mean(s_durations), statistics.mean(c_durations)])
    rows.append(["stdev", statistics.stdev(s_durations), statistics.stdev(c_durations)])
    rows.append(["statistical_difference", p, ""])
    rows.append(["effect_size", eff_size, eff_desc])

    fm.write_csv(path=os.path.join("evaluation", "response_time.csv"), data=rows, header=header)
    
    plt.figure(figsize=(8,6))
    means = [np.mean(s_durations), np.mean(c_durations)]
    std_devs = [np.std(s_durations), np.std(c_durations)]
    sns.barplot(data=[np.array(s_durations), np.array(c_durations)], palette=["#FFBA49", "#20A39E"], ci=None)
    plt.errorbar(x=[0, 1], y=means, yerr=std_devs, fmt='none', c='black', capsize=5, capthick=2, lw=2)
    plt.xticks([0, 1], ['Segmented', 'Combined'])
    plt.ylabel("in seconds")
    # Define coordinates for significance line
    x1, x2 = 0.1, 0.9  # x-coordinates of the two bars
    y = max(means) + 0.5  # y-coordinate above the bars for the significance line
    plt.plot([x1, x2], [y, y], color='black', linestyle='--', linewidth=1)  # Horizontal line
    plt.plot([x1, x1], [means[0], y], color='black', linestyle='--', linewidth=1)  # Left vertical line
    plt.plot([x2, x2], [means[1], y], color='black', linestyle='--', linewidth=1)  # Right vertical line
    plt.text((x1 + x2) / 2, y, '*', fontsize=20, ha='center', va='bottom', color='black')  # Asterisk above the line
    # plt.title('Box Plot with Mean and Standard Deviation')
    plt.show()
    pass

if __name__=="__main__":
    response_time_evaluation()
    correct_rate_evaluation()
    pass