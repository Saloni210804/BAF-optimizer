import streamlit as st
import pandas as pd

# Constants
MAX_STACK_HEIGHT = 4450  # mm
MAX_STACK_WEIGHT = 75  # kg
MIN_COILS = 4
MAX_COILS = 5

st.title("BAF Line Stack Optimizer")

uploaded_file = st.file_uploader("Upload Excel File with Width, Grade, and Weight", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)

    required_cols = {'Width', 'Grade', 'Weight'}
    if not required_cols.issubset(df.columns):
        st.error("Excel must contain 'Width', 'Grade', and 'Weight' columns.")
    else:
        st.success("File uploaded successfully!")

        # Convert Width and Weight to numeric to prevent sorting errors
        df['Width'] = pd.to_numeric(df['Width'], errors='coerce')
        df['Weight'] = pd.to_numeric(df['Weight'], errors='coerce')
        df.dropna(subset=['Width', 'Weight'], inplace=True)

        # Store original grade in a new column
        df['Original Grade'] = df['Grade']

        # Normalize grade for grouping
        df['Normalized Grade'] = df['Grade'].replace({
            'DR-08': 'T-57',
            'TS-480': 'T-57',
            'DR-75': 'T-57'
        })

        total_input_coils = len(df)
        stacks = []
        waiting = []

        # Counters
        stack_4_count = 0
        stack_5_count = 0
        stack_lt_4000 = 0
        stack_ge_4000 = 0

        # Group by normalized grade
        for grade, group in df.groupby("Normalized Grade"):
            group = group.sort_values(by="Width", ascending=False).reset_index(drop=True)
            used = [False] * len(group)

            while True:
                stack = []
                total_width = 0
                total_weight = 0

                for i in range(len(group)):
                    if not used[i] and len(stack) < MAX_COILS:
                        coil_width = group.loc[i, "Width"]
                        coil_weight = group.loc[i, "Weight"]
                        coil_original_grade = group.loc[i, "Original Grade"]

                        if (total_width + coil_width <= MAX_STACK_HEIGHT and
                            total_weight + coil_weight <= MAX_STACK_WEIGHT):

                            stack.append({
                                "Width": coil_width,
                                "Weight": coil_weight,
                                "Grade": coil_original_grade
                            })
                            total_width += coil_width
                            total_weight += coil_weight
                            used[i] = True

                if len(stack) >= MIN_COILS:
                    stacks.append({
                        "Grade": grade,
                        "Total Width": total_width,
                        "Total Weight": total_weight,
                        "Coils": stack
                    })

                    # Count stats
                    if len(stack) == 4:
                        stack_4_count += 1
                    elif len(stack) == 5:
                        stack_5_count += 1

                    if total_width < 4000:
                        stack_lt_4000 += 1
                    else:
                        stack_ge_4000 += 1
                else:
                    break  # No valid stack can be made anymore

            # Add remaining unused coils to waiting list
            for i in range(len(group)):
                if not used[i]:
                    waiting.append({
                        "Grade": group.loc[i, "Original Grade"],
                        "Width": group.loc[i, "Width"],
                        "Weight": group.loc[i, "Weight"]
                    })
                    # Summary
        st.header("Summary")
        st.write(f"Total Input Coils: {total_input_coils}")
        st.write(f"Total Stacks: {len(stacks)}")
        st.write(f"4-Coil Stacks: {stack_4_count}")
        st.write(f"5-Coil Stacks: {stack_5_count}")
        st.write(f"Stacks < 4000 mm: {stack_lt_4000}")
        st.write(f"Stacks ≥ 4000 mm: {stack_ge_4000}")
        if stacks:
            avg_stack_height = sum(stack['Total Width'] for stack in stacks) / len(stacks)
            avg_stack_weight = sum(stack['Total Weight'] for stack in stacks) / len(stacks)
            st.write(f"Average Stack Height: {round(avg_stack_height, 2)} mm")
            st.write(f"Average Stack Weight: {round(avg_stack_weight, 2)} kg")
        else:
            st.write("Average Stack Height: N/A")
            st.write("Average Stack Weight: N/A")

        # Show Stacks
        st.header("Optimized Stacks")
        for i, stack in enumerate(stacks, 1):
            st.markdown(
                f"Stack {i}: Grade {stack['Grade']}, "
                f"Total Width: {stack['Total Width']} mm, "
                f"Total Weight: {round(stack['Total Weight'], 2)} kg"
            )
            stack_df = pd.DataFrame(stack['Coils']).reset_index(drop=True)
            stack_df.index += 1  # Start numbering from 1
            st.dataframe(stack_df)

        # Show Waiting Coils
        st.header("Waiting Coils")
        if waiting:
            waiting_df = pd.DataFrame(waiting).reset_index(drop=True)
            waiting_df.index += 1  # Start numbering from 1
            st.dataframe(waiting_df)
        else:
            st.success("✅ All coils used in valid stacks!")

        st.write(f"Waiting Coils: {len(waiting)}")