include Savage::Directions

class PenUp; end
class PenDown; end

class Savage::Directions::Point
  def inspect
    "(x:#{x}, y:#{y})"
  end

  def *(a)
    self.class.new(x * a, y * a)
  end

  def +(p)
    self.class.new(x + p.x, y + p.y)
  end

  def -(p)
    self.class.new(x - p.x, y - p.y)
  end

  def round(*args)
    self.class.new(x.round(*args), y.round(*args))
  end

  def distance_to(p)
    Math.sqrt((x - p.x) ** 2 + (y - p.y) ** 2)
  end
end

def interpolate_spline(p0, p1, p2, p3, t)
  p0 * (1.0 - t)**3 + p1 * 3 * (1.0 - t)**2 * t + p2 * 3 * (1.0 - t) * t**2 + p3 * t**3
end

def segment_spline(p0, p1, p2, p3)
  t_count = 4
  raise 'p0' unless p0
  raise 'p1' unless p1
  raise 'p2' unless p2
  raise 'p3' unless p3
  while (dist = p0.distance_to(interpolate_spline(p0, p1, p2, p3, 1 / (t_count + 1)))) > 1.0
    t_count *= 2
  end
  ts = (1..t_count).map{|t| t.to_f / (t_count + 1)}
  [p0] + ts.map{|t| interpolate_spline(p0, p1, p2, p3, t)} + [p3]
end

class Savage::Path
  def to_line_segments
    start_position = nil
    current_position = Point.new(0, 0)
    reflection = nil
    subpaths.map do |subpath|
      subpath.directions.map do |direction|
        reflection = nil unless direction.is_a?(CubicCurveTo)
        case direction
        when MoveTo
          if direction.absolute?
            current_position = direction.target
            start_position = current_position
          else
            current_position += direction.target
            start_position = current_position
          end
          [PenUp, direction.target]
        when LineTo
          if direction.absolute?
            current_position = direction.target
          else
            current_position += direction.target
          end
          [PenDown, direction.target]
        when VerticalTo
          if direction.absolute?
            current_position.y = direction.target
          else
            current_position.y += direction.target
          end
          [PenDown, direction.target]
        when HorizontalTo
          if direction.absolute?
            current_position.x = direction.target
          else
            current_position.x += direction.target
          end
          [PenDown, direction.target]
        when CubicCurveTo
          old_position = current_position.clone
          if direction.absolute?
            current_position = direction.target
            c1 = direction.control_1 || reflection
            c2 = direction.control_2
          else
            current_position += direction.target
            c1 = (direction.control_1 && (direction.control_1 + old_position)) || reflection
            c2 = direction.control_2 + old_position
          end
          reflection = (c2 - current_position) * -1 + current_position
          [PenDown] + segment_spline(old_position, c1, c2, current_position)
        when ClosePath
          [PenDown, start_position]
        else
          direction.inspect
          raise direction.inspect
        end
      end
    end.flatten
  end
end

def gcodify(filename)
  svg_text = File.read(filename)
  doc = Nokogiri.XML(svg_text)
  path_els = doc.search('path')
  paths = path_els.map {|el| Savage::Parser.parse el['d']}

  pendown = false
  segments = paths.map(&:to_line_segments).flatten
  segments.map do |segment|
    case segment
    when Point
      "G1 X#{segment.x} Y#{segment.y}"
    when PenDown
      unless pendown
        pendown = true
        "G1 Z15"
      end
    when PenUp
      if pendown
        pendown = false
        "G1 Z5"
      end
    else
      raise segment.inspect
    end
  end.compact
end
