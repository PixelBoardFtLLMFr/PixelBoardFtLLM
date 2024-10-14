import file_manager as fm
import llm
import argparse
import os

# compared_pes = [[llm.PEType.ZERO_SHOT],
#                 [llm.PEType.ZERO_SHOT_COT],
#                 [llm.PEType.FEW_SHOT],
#                 [llm.PEType.FEW_SHOT, llm.PEType.ZERO_SHOT_COT],
#                 [llm.PEType.NULL_SHOT],
#                 [llm.PEType.NULL_SHOT_COT]]
compared_pes = [[llm.PEType.NULL_SHOT],
                [llm.PEType.NULL_SHOT_COT]]
segmented_pts = [llm.PromptType.ARM,
                llm.PromptType.LEG,
                llm.PromptType.HEAD,
                llm.PromptType.HEIGHT,
                llm.PromptType.FE,
                llm.PromptType.PARTICLE]

def get_pe_dir(pes:list[str])->str:    
    dirname=pes[0]
    for i, pe in enumerate(pes):
        if i>0:
            dirname=f"{dirname}-{pe}"
    return dirname

def run_segmented_prompts(instructions:list[str], myllm:llm.Llm):
    root_dir=os.path.join("responses", "segmented")

    for pes in compared_pes:
        target_dir=os.path.join(root_dir, get_pe_dir(pes=pes))
        if not os.path.exists(target_dir):
            os.makedirs(target_dir)

        for i, instruction in enumerate(instructions):

            for pt in segmented_pts:
                myllm.push_prompt(prompt_template=llm.build_my_prompt(kind=pt, pes=pes), 
                                  user_input=instruction, 
                                  key=pt)

            # Executing Prompts ...
            print(f"run segmented: {pes} {(i+1)}")
            responses = myllm.eval_execute_prompts()

            arms_filepath=os.path.join(target_dir, f"{(i+1)}-arms.json")
            legs_filepath=os.path.join(target_dir, f"{(i+1)}-legs.json")
            head_filepath=os.path.join(target_dir, f"{(i+1)}-head.json")
            y_pos_filepath=os.path.join(target_dir, f"{(i+1)}-y_position.json")
            fe_filepath=os.path.join(target_dir, f"{(i+1)}-facial_expression.json")
            vfx_filepath=os.path.join(target_dir, f"{(i+1)}-visual_effect.json")

            fm.write_json(path=arms_filepath, data=responses[llm.PromptType.ARM])
            fm.write_json(path=legs_filepath, data=responses[llm.PromptType.LEG])
            fm.write_json(path=head_filepath, data=responses[llm.PromptType.HEAD])
            fm.write_json(path=y_pos_filepath, data=responses[llm.PromptType.HEIGHT])
            fm.write_json(path=fe_filepath, data=responses[llm.PromptType.FE])
            fm.write_json(path=vfx_filepath, data=responses[llm.PromptType.PARTICLE])
    pass

def run_combined_prompts(instructions:list[str], myllm:llm.Llm):
    root_dir=os.path.join("responses", "combined")

    for pes in compared_pes:
        target_dir=os.path.join(root_dir, get_pe_dir(pes=pes))
        if not os.path.exists(target_dir):
            os.makedirs(target_dir)

        for i, instruction in enumerate(instructions):
            myllm.push_prompt(prompt_template=llm.build_my_prompt(kind=llm.PromptType.COMBINED, pes=pes), 
                              user_input=instruction, 
                              key=llm.PromptType.COMBINED)
            
            # Executing Prompts ...
            print(f"run combined: {pes} {(i+1)}")
            responses = myllm.eval_execute_prompts()

            combined_filepath=os.path.join(target_dir, f"{(i+1)}-combined.json")
            fm.write_json(path=combined_filepath, data=responses[llm.PromptType.COMBINED])
    pass

def main():
    arg_parser = argparse.ArgumentParser(prog="ppp", description="response gathering")
    arg_parser.add_argument("-k", "--keyfile", action='store', default="./key.txt",
                            help="file that contain LLM API key, defaults to ./key.txt")
    arg_parser.add_argument("-m", "--modelname", action='store', default="gpt-4o-mini-2024-07-18",
                            choices=["gpt-3.5-turbo", "gpt-4o-mini", "gpt-4o-mini-2024-07-18"], help="ChatGPT version to use")

    args = arg_parser.parse_args()
    myllm = llm.Llm(keyfile =args.keyfile, model_name=args.modelname)
    instructions = fm.read_text('./instructions/chatgpt.txt').splitlines()
    # run_segmented_prompts(instructions=instructions, myllm=myllm)
    run_combined_prompts(instructions=instructions, myllm=myllm)
    pass

if __name__=="__main__":
    main()