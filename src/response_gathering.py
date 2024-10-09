import file_manager as fm
import llm
import argparse
import os

def run_segmented_prompts(instructions:list[str], myllm:llm.Llm):
    root_dir=os.path.join("responses", "segmented")
    for i, instruction in enumerate(instructions):
        ## Angles
        limb_prompt_types = [llm.PromptType.ARM, llm.PromptType.LEG, llm.PromptType.HEAD]
        user_prompt = f"{instruction}"

        for kind in limb_prompt_types:
            myllm.push_prompt(llm.build_prompt(kind), user_prompt, f"ANGLE{kind}")

        ## Height
        myllm.push_prompt(llm.height_prompt, user_prompt, "HEIGHT")

        ## Facial Expression
        myllm.push_prompt(llm.build_prompt(llm.PromptType.FACE), user_prompt, "FE")

        ## Particle
        myllm.push_prompt(llm.particle_prompt, user_prompt, "PARTICLE")

        # Executing Prompts ...
        responses = myllm.eval_execute_prompts()

        arms_filepath=os.path.join(root_dir, f"{(i+1)}-arms.json")
        legs_filepath=os.path.join(root_dir, f"{(i+1)}-legs.json")
        head_filepath=os.path.join(root_dir, f"{(i+1)}-head.json")
        y_pos_filepath=os.path.join(root_dir, f"{(i+1)}-y_position.json")
        fe_filepath=os.path.join(root_dir, f"{(i+1)}-facial_expression.json")
        vfx_filepath=os.path.join(root_dir, f"{(i+1)}-visual_effect.json")

        fm.write_json(path=arms_filepath, data=responses["ANGLE0"])
        fm.write_json(path=legs_filepath, data=responses["ANGLE1"])
        fm.write_json(path=head_filepath, data=responses["ANGLE2"])
        fm.write_json(path=y_pos_filepath, data=responses["HEIGHT"])
        fm.write_json(path=fe_filepath, data=responses["FE"])
        fm.write_json(path=vfx_filepath, data=responses["PARTICLE"])
    pass

def run_compiled_prompts(instructions:list[str], myllm:llm.Llm):
    root_dir=os.path.join("responses", "compiled")
    for i, instruction in enumerate(instructions):
        user_prompt = f"{instruction}"
        myllm.push_prompt(llm.all_prompt, user_prompt, "COMPILED")
        # Executing Prompts ...
        responses = myllm.eval_execute_prompts()
        compiled_filepath=os.path.join(root_dir, f"{(i+1)}-compiled.json")
        fm.write_json(path=compiled_filepath, data=responses["COMPILED"])
    pass

def main():
    arg_parser = argparse.ArgumentParser(prog="ppp", description="response gathering")
    arg_parser.add_argument("-k", "--keyfile", action='store', default="./key.txt",
                            help="file that contain LLM API key, defaults to ./key.txt")
    arg_parser.add_argument("-v", "--llm-version", action='store', default="4o-mini",
                            choices=["3.5-turbo", "4o-mini", "4o-mini-2024-07-18"], help="ChatGPT version to use")

    args = arg_parser.parse_args()
    myllm = llm.Llm(args.keyfile, args.llm_version)
    instructions=fm.read_text('./instructions/chatgpt.txt').splitlines()
    # run_segmented_prompts(instructions=instructions, myllm=myllm)
    run_compiled_prompts(instructions=instructions, myllm=myllm)
    pass

if __name__=="__main__":
    main()