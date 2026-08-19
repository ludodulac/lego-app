"""End-to-end M0 pipeline from BuildingModel to viewer export JSON."""
from __future__ import annotations
import argparse
from pathlib import Path
from brickhouse.building.models import BuildingModel
from brickhouse.building.validation import load_building_model
from brickhouse.bricks.assembly import generate_assembly_plan
from brickhouse.bricks.bom import generate_bom
from brickhouse.bricks.brick_model import generate_brick_model
from brickhouse.bricks.building_layout import generate_building_brick_shell
from brickhouse.bricks.export import BrickExportBundle, create_export_bundle, export_bundle_json
from brickhouse.bricks.facade_details import generate_window_surrounds
from brickhouse.bricks.roof import generate_spatial_gable_roof
from brickhouse.bricks.spatial import generate_spatial_brick_shell
from brickhouse.bricks.windows import generate_window_assemblies
from brickhouse.geometry import generate_building_geometry
DEFAULT_FRONT_WIDTH_STUDS=48

def run_m0_pipeline_model(building:BuildingModel,*,front_width_studs:int=DEFAULT_FRONT_WIDTH_STUDS)->BrickExportBundle:
    """Run the deterministic M0 engine directly from an already validated BuildingModel."""
    if front_width_studs<=0: raise ValueError("front_width_studs must be positive")
    geometry=generate_building_geometry(building)
    building_shell=generate_building_brick_shell(geometry,front_width_studs)
    spatial_shell=generate_spatial_brick_shell(building_shell)
    window_parts,fitted_window_ids=generate_window_assemblies(building,building_shell)
    facade_details=generate_window_surrounds(building,building_shell,skip_opening_ids=fitted_window_ids)
    spatial_roof=generate_spatial_gable_roof(geometry,building_shell)
    brick_model=generate_brick_model(spatial_shell,spatial_roof,facade_details,window_parts)
    bom=generate_bom(brick_model); assembly_plan=generate_assembly_plan(brick_model)
    return create_export_bundle(brick_model,bom,assembly_plan)

def run_m0_pipeline(input_path:str|Path,*,front_width_studs:int=DEFAULT_FRONT_WIDTH_STUDS)->BrickExportBundle:
    building=load_building_model(input_path); return run_m0_pipeline_model(building,front_width_studs=front_width_studs)

def write_m0_export(input_path:str|Path,output_path:str|Path,*,front_width_studs:int=DEFAULT_FRONT_WIDTH_STUDS)->BrickExportBundle:
    bundle=run_m0_pipeline(input_path,front_width_studs=front_width_studs); destination=Path(output_path); destination.parent.mkdir(parents=True,exist_ok=True); destination.write_text(export_bundle_json(bundle)+"\n",encoding="utf-8"); return bundle

def build_parser()->argparse.ArgumentParser:
    parser=argparse.ArgumentParser(prog="brickhouse-m0",description="Generate a BrickHouse M0 BrickModel/BOM/AssemblyPlan JSON export from a BuildingModel JSON file.")
    parser.add_argument("input",type=Path,help="BuildingModel JSON input"); parser.add_argument("output",type=Path,help="Output export JSON path")
    parser.add_argument("--front-width-studs",type=int,default=DEFAULT_FRONT_WIDTH_STUDS,help=f"target front facade width in studs (default: {DEFAULT_FRONT_WIDTH_STUDS})")
    return parser

def main(argv:list[str]|None=None)->int:
    args=build_parser().parse_args(argv); bundle=write_m0_export(args.input,args.output,front_width_studs=args.front_width_studs)
    print(f"Generated {args.output}: {bundle.bom.total_parts} parts, {bundle.bom.unique_part_types} canonical types, {bundle.assembly_plan.total_steps if bundle.assembly_plan else 0} assembly steps")
    return 0
if __name__=="__main__": raise SystemExit(main())
