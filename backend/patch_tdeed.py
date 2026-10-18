from pathlib import Path
import json

root = Path("/opt/T-DEED")
model = root / "model" / "model.py"
text = model.read_text()
text = text.replace("pretrained=True", "pretrained=False")
text = text.replace("def __init__(self, device='cuda', args=None):", "def __init__(self, device='cpu', args=None):")
model.write_text(text)

inference = root / "inference.py"
text = inference.read_text()
old = """model.load(torch.load(os.path.join(
        os.getcwd(), 'checkpoints', args.model.split('_')[0], args.model, 'checkpoint_best.pt')))"""
new = """checkpoint_path = os.environ.get(
        'TDEED_CHECKPOINT_PATH',
        os.path.join(os.getcwd(), 'checkpoints', args.model.split('_')[0], args.model, 'checkpoint_best.pt')
    )
    model.load(torch.load(checkpoint_path, map_location='cpu'))"""
if old not in text:
    raise SystemExit("Could not safely patch checkpoint loading in upstream inference.py")
inference.write_text(text.replace(old, new))

config = root / "config" / "SoccerNetBall" / "SoccerNetBall_challenge1.json"
data = json.loads(config.read_text())
# Keep CPU peak memory manageable for a small web-service instance.
data["batch_size"] = 1
data["num_workers"] = 0
config.write_text(json.dumps(data, indent=2) + "\n")
print("Patched T-DEED for CPU inference, configured checkpoint path, and lower memory use.")
