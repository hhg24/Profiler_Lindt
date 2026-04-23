import pandas as pd
from typing import Iterable

def write_to_excel(data, file_name, sheet_names=None):
    """
    Write a DataFrame or a list of DataFrames to an Excel file with optional sheet names.

    Parameters:
    data (pd.DataFrame or list of pd.DataFrame): The DataFrame(s) to write to the Excel file.
    file_path (str): The path to save the Excel file.
    sheet_names (str or list of str, optional): The name(s) of the sheet(s). If not provided, default names will be used.

    Returns:
    None
    """
    # Define the file path
    file_path = f"./results/{file_name}"
    # Create an Excel writer object
    with pd.ExcelWriter(file_path, engine='xlsxwriter') as writer:
        if isinstance(data, pd.DataFrame):
            # Handle a single DataFrame
            sheet_name = sheet_names if isinstance(sheet_names, str) else 'Sheet1'
            data.to_excel(writer, sheet_name=sheet_name, index=False)
        elif isinstance(data, list):
            # Handle a list of DataFrames
            if sheet_names is None:
                # Default sheet names if none are provided
                sheet_names = [f"Sheet{i + 1}" for i in range(len(data))]
            elif not isinstance(sheet_names, list) or len(sheet_names) != len(data):
                raise ValueError("sheet_names must be a list with the same length as the data list.")
            
            for df, sheet_name in zip(data, sheet_names):
                if not isinstance(df, pd.DataFrame):
                    raise ValueError(f"All elements in the data list must be DataFrames.")
                df.to_excel(writer, sheet_name=sheet_name, index=False)
        else:
            raise ValueError("Input data must be a DataFrame or a list of DataFrames.")


DEFAULT_PROFILER_CHAPTERS = [
    "Descriptive feature",
    "Purchasing behavior",
    "Sociodemographic (% Customers)",
    "Month of registration (% Customers)",
    "Marketing consent (% Customers)",
    "Channel preference (% Customers)",
    "Website activity (General)",
    "Devices & App Usage (% Sessions)",
    "Session Cluster (% Sessions)",
    "Primary Channel Group (% of Sessions)",
    "Traffic Source (% of Sessions)",
    "Lifecycle",
    "RFM",
    "Season (% Gross Sales)",
    "Trimester (% Gross Sales)",
    "Month (% Gross Sales)",
    "Week days (% Gross Sales)",
    "Time (% Gross Sales)",
    "Registration Channel",
    "Shopformats Gross Sales Distribution",
    "IPA1 - Seasonal or Permanent",
    "IPA2 - Subbrand (Top 15 dynamic)",
    "IPA4 - Packaging format",
    "IPA5 - Weight",
    "IPA6 - Taste",
]


def _as_float(value):
    if pd.isna(value):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    value_str = str(value).strip()
    if not value_str:
        return None
    normalized = value_str.replace("%", "").replace(" ", "")
    if "," in normalized and "." in normalized:
        normalized = normalized.replace(",", "")
    else:
        normalized = normalized.replace(",", ".")
    try:
        return float(normalized)
    except ValueError:
        return None


def _looks_like_percentage(values: Iterable, chapter: str, kpi_name: str) -> bool:
    if "%" in chapter or "%" in kpi_name:
        return True
    return any(isinstance(v, str) and "%" in v for v in values)


def _format_value(value: float, percentage: bool) -> str:
    if percentage:
        if 0 <= value <= 1:
            value *= 100
        return f"{value:.1f}%"
    return f"{value:.2f}"


def generate_profiler_interpretations(
    profiler_df: pd.DataFrame,
    chapters: Iterable[str] = None,
    feature_column: str = "Descriptive feature",
    comments_column: str = "Comments",
    overwrite_comments: bool = True,
) -> pd.DataFrame:
    """
    Generate business-English chapter-based interpretations for a Profiler sheet.

    Interpretation is generated from the columns located between the feature and comments columns.
    """
    if feature_column not in profiler_df.columns:
        raise ValueError(f"Column '{feature_column}' not found in profiler dataframe.")
    if comments_column not in profiler_df.columns:
        raise ValueError(f"Column '{comments_column}' not found in profiler dataframe.")

    result_df = profiler_df.copy()

    chapter_set = set(chapters or DEFAULT_PROFILER_CHAPTERS)
    feature_idx = result_df.columns.get_loc(feature_column)
    comments_idx = result_df.columns.get_loc(comments_column)
    if comments_idx <= feature_idx + 1:
        raise ValueError(
            f"'{comments_column}' must be positioned after '{feature_column}' with data columns in between."
        )

    data_columns = list(result_df.columns[feature_idx + 1 : comments_idx])
    current_chapter = None

    for row_idx, row in result_df.iterrows():
        feature = row.get(feature_column)
        if pd.isna(feature) or str(feature).strip() == "":
            continue

        feature_text = str(feature).strip()
        if feature_text in chapter_set:
            current_chapter = feature_text
            continue

        if not current_chapter:
            continue

        if not overwrite_comments and pd.notna(row.get(comments_column)) and str(row.get(comments_column)).strip():
            continue

        numeric_values = []
        raw_values = []
        for column in data_columns:
            parsed = _as_float(row.get(column))
            if parsed is not None:
                numeric_values.append((column, parsed))
                raw_values.append(row.get(column))

        if not numeric_values:
            continue

        max_group, max_value = max(numeric_values, key=lambda item: item[1])
        min_group, min_value = min(numeric_values, key=lambda item: item[1])
        avg_value = sum(value for _, value in numeric_values) / len(numeric_values)
        as_percentage = _looks_like_percentage(raw_values, current_chapter, feature_text)

        if max_group == min_group or abs(max_value - min_value) < 1e-9:
            interpretation = (
                f"Within {current_chapter}, {feature_text} is broadly consistent across customer groups "
                f"at around {_format_value(avg_value, as_percentage)}."
            )
        else:
            interpretation = (
                f"Within {current_chapter}, {feature_text} is strongest for {max_group} "
                f"({_format_value(max_value, as_percentage)}) and lowest for {min_group} "
                f"({_format_value(min_value, as_percentage)}), with an average of "
                f"{_format_value(avg_value, as_percentage)} across the selected groups."
            )

        result_df.at[row_idx, comments_column] = interpretation

    return result_df
